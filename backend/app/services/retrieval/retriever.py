"""Hybrid retrieval over a single video's transcript chunks.

1. Semantic search: cosine distance on pgvector embeddings (exact scan, filtered by video).
2. Keyword search: PostgreSQL full-text ranking, which catches names and exact terms.
3. Reciprocal-rank fusion of both lists (when reranking is enabled).
4. Neighbor expansion so answers see the surrounding conversation.
5. For whole-video questions, timeline coverage so summaries aren't based on a few fragments.
"""

import logging
import re
import uuid
from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.repositories import ChunkRepository

logger = logging.getLogger(__name__)

_RRF_K = 60
_STOPWORDS = set(
    """a an the and or but if of to in on at by for with about from into over after before is are was were be been
    being do does did done have has had what which who whom whose when where why how this that these those it its
    i you he she they we me him her them us my your his their our can could should would will shall may might must
    not no yes so than then there here just also very more most some any all each both few many much such own same
    tell explain describe say says said talk talks talked video speaker mention mentioned please give me""".split()
)


@dataclass
class RetrievedChunk:
    chunk_index: int
    content: str
    start_time: float
    end_time: float
    score: float | None
    source: str  # "match" | "neighbor" | "coverage"

    def to_dict(self) -> dict:
        return asdict(self)


def _keyword_query(question: str) -> str | None:
    words = [w for w in re.findall(r"\w+", question.lower()) if len(w) > 1 and w not in _STOPWORDS]
    words = list(dict.fromkeys(words))[:12]
    return " | ".join(words) if words else None


class Retriever:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    async def _semantic(self, video_id: uuid.UUID, model: str, vector: list[float], limit: int) -> list[tuple]:
        result = await self.session.execute(
            text(
                """
                SELECT chunk_index, content, start_time, end_time, 1 - (embedding <=> CAST(:q AS vector)) AS similarity
                FROM transcript_chunks
                WHERE video_id = :vid AND embedding_model = :model
                ORDER BY embedding <=> CAST(:q AS vector)
                LIMIT :limit
                """
            ),
            {"q": str(vector), "vid": video_id, "model": model, "limit": limit},
        )
        return list(result.all())

    async def _keyword(self, video_id: uuid.UUID, question: str, limit: int) -> list[tuple]:
        query = _keyword_query(question)
        if not query:
            return []
        result = await self.session.execute(
            text(
                """
                SELECT chunk_index, ts_rank_cd(content_tsv, to_tsquery('simple', :q)) AS rank
                FROM transcript_chunks
                WHERE video_id = :vid AND content_tsv @@ to_tsquery('simple', :q)
                ORDER BY rank DESC
                LIMIT :limit
                """
            ),
            {"q": query, "vid": video_id, "limit": limit},
        )
        return list(result.all())

    async def retrieve(
        self,
        *,
        video_id: uuid.UUID,
        embedding_model: str,
        question: str,
        query_vector: list[float],
        total_chunks: int,
        broad: bool = False,
    ) -> list[RetrievedChunk]:
        s = self.settings
        pool = max(s.candidate_pool_size, s.top_k)
        semantic = await self._semantic(video_id, embedding_model, query_vector, pool)
        by_index = {row.chunk_index: row for row in semantic}

        relevant = [row for row in semantic if row.similarity >= s.similarity_threshold]
        if not relevant:
            # Let the model judge weak matches rather than answering with no context at all.
            relevant = semantic[:2]

        if s.rerank_enabled:
            scores: dict[int, float] = {}
            for rank, row in enumerate(relevant):
                scores[row.chunk_index] = scores.get(row.chunk_index, 0) + 1 / (_RRF_K + rank)
            for rank, row in enumerate(await self._keyword(video_id, question, pool)):
                scores[row.chunk_index] = scores.get(row.chunk_index, 0) + 1 / (_RRF_K + rank)
            ranked = sorted(scores, key=scores.get, reverse=True)
        else:
            ranked = [row.chunk_index for row in relevant]

        top = ranked[: s.top_k]
        repo = ChunkRepository(self.session)
        budget = s.max_context_chars

        selected: dict[int, RetrievedChunk] = {}

        def add(chunk, source: str, score: float | None) -> bool:
            nonlocal budget
            if chunk.chunk_index in selected:
                return True
            if len(chunk.content) > budget:
                return False
            budget -= len(chunk.content)
            selected[chunk.chunk_index] = RetrievedChunk(
                chunk.chunk_index, chunk.content, chunk.start_time, chunk.end_time, score, source
            )
            return True

        if broad:
            all_chunks = list(await repo.list_for_video(video_id))
            total_chars = sum(len(c.content) for c in all_chunks)
            if total_chars <= budget:
                for c in all_chunks:
                    sim = by_index[c.chunk_index].similarity if c.chunk_index in by_index else None
                    add(c, "match" if c.chunk_index in top else "coverage", sim)
                return sorted(selected.values(), key=lambda c: c.chunk_index)

        top_chunks = {c.chunk_index: c for c in await repo.get_by_indexes(video_id, top)}
        for idx in top:
            if idx in top_chunks:
                add(top_chunks[idx], "match", by_index[idx].similarity if idx in by_index else None)

        if broad:
            # Evenly sample across the timeline with the remaining budget.
            avg = max(1, sum(len(c.content) for c in all_chunks) // max(1, len(all_chunks)))
            slots = max(0, budget // avg)
            if slots and all_chunks:
                step = max(1, len(all_chunks) / slots)
                position = 0.0
                while int(position) < len(all_chunks):
                    add(all_chunks[int(position)], "coverage", None)
                    position += step
        elif s.neighbor_window > 0:
            wanted = sorted(
                {
                    n
                    for idx in top
                    for n in range(idx - s.neighbor_window, idx + s.neighbor_window + 1)
                    if 0 <= n < total_chunks and n not in selected
                }
            )
            for c in await repo.get_by_indexes(video_id, wanted):
                add(c, "neighbor", None)

        logger.debug("Retrieved %d chunks (broad=%s)", len(selected), broad)
        return sorted(selected.values(), key=lambda c: c.chunk_index)
