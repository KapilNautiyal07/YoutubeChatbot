"""RAG orchestration: rewrite -> embed -> retrieve -> prompt -> generate -> persist."""

import json
import logging
import re
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError, ProviderError
from app.db.models import Conversation, Video, VideoStatus
from app.db.repositories import ChunkRepository, ConversationRepository, VideoRepository
from app.services.embeddings.factory import get_embedder_for
from app.services.llm.base import ChatMessage, LLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.rag import prompts
from app.services.retrieval.retriever import RetrievedChunk, Retriever

logger = logging.getLogger(__name__)

_BROAD_RE = re.compile(
    r"\b(summar\w*|overview|tl;?dr|recap|outline|gist|key (points|takeaways|ideas|lessons|concepts)|"
    r"main (points|ideas|topics|concepts|themes|argument|message|takeaways)|takeaways|conclusions?|"
    r"(whole|entire|full) video|what('s| is) (this|the) video about|topics (covered|discussed)|chapters|structure)\b",
    re.IGNORECASE,
)


@dataclass
class PreparedChat:
    video: Video
    conversation: Conversation
    provider: LLMProvider
    model: str
    messages: list[ChatMessage]
    chunks: list[RetrievedChunk]
    user_message_id: uuid.UUID


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    return json.loads(match.group(0) if match else raw)


def serialize_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """Compact record of retrieved context stored with each answer."""
    return [
        {
            "chunk_index": c.chunk_index,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "score": round(c.score, 4) if c.score is not None else None,
            "source": c.source,
            "content": c.content if c.source == "match" else c.content[:240],
        }
        for c in chunks
    ]


class RAGPipeline:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.videos = VideoRepository(session)
        self.conversations = ConversationRepository(session)

    async def _rewrite(
        self, provider: LLMProvider, model: str, history: list[ChatMessage], question: str
    ) -> tuple[str, bool]:
        heuristic_broad = bool(_BROAD_RE.search(question))
        if not history:
            return question, heuristic_broad
        transcript = "\n".join(f"{m.role}: {m.content[:600]}" for m in history[-6:])
        try:
            raw = await provider.generate(
                prompts.CONDENSE_SYSTEM_PROMPT,
                [ChatMessage("user", f"Conversation:\n{transcript}\n\nNewest message: {question}")],
                model=model,
                json_mode=True,
            )
            data = _parse_json(raw)
            query = str(data.get("query") or question).strip() or question
            broad = heuristic_broad or data.get("scope") == "broad"
            logger.info("Rewrote follow-up %r -> %r (broad=%s)", question[:80], query[:120], broad)
            return query, broad
        except (ProviderError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Query rewrite failed, using original question: %s", exc)
            return question, heuristic_broad

    async def prepare(
        self, *, video_id: uuid.UUID, conversation_id: uuid.UUID | None, question: str,
        provider_name: str | None, model: str | None
    ) -> PreparedChat:
        video = await self.videos.get(video_id)
        if video is None:
            raise NotFoundError("Video not found.")
        if video.status != VideoStatus.READY.value:
            raise ConflictError("This video is still being processed. Please wait until it's ready.")

        if conversation_id:
            conversation = await self.conversations.get(conversation_id)
            if conversation is None or conversation.video_id != video.id:
                raise NotFoundError("Conversation not found for this video.")
        else:
            title = question.strip().replace("\n", " ")
            conversation = await self.conversations.create(video.id, title[:80] + ("…" if len(title) > 80 else ""))

        provider = get_llm_provider(provider_name, self.settings)
        model_name = model or provider.default_model

        history_rows = await self.conversations.recent_messages(conversation.id, self.settings.history_messages)
        history = [ChatMessage(m.role, m.content) for m in history_rows]

        query, broad = await self._rewrite(provider, model_name, history, question)

        embedder = get_embedder_for(video.embedding_model or "", self.settings)
        query_vector = await embedder.embed_query(query)

        retriever = Retriever(self.session, self.settings)
        chunks = await retriever.retrieve(
            video_id=video.id,
            embedding_model=video.embedding_model or "",
            question=query,
            query_vector=query_vector,
            total_chunks=video.chunk_count,
            broad=broad,
        )
        whole = broad and len(chunks) == video.chunk_count

        context = prompts.build_context_message(
            title=video.title,
            channel=video.channel_name,
            duration=video.duration,
            language=video.transcript_language,
            excerpts=chunks,
            question=question if query == question else f"{question}\n(Interpreted as: {query})",
            whole_transcript=whole,
        )
        messages = history + [ChatMessage("user", context)]

        user_message = await self.conversations.add_message(conversation.id, "user", question)
        await self.session.commit()

        return PreparedChat(video, conversation, provider, model_name, messages, chunks, user_message.id)

    async def save_answer(self, prepared: PreparedChat, answer: str):
        message = await self.conversations.add_message(
            prepared.conversation.id,
            "assistant",
            answer,
            provider=prepared.provider.name,
            model=prepared.model,
            retrieved_chunks=serialize_sources(prepared.chunks),
        )
        # Touch the conversation so it sorts as most recent.
        await self.session.execute(
            update(Conversation).where(Conversation.id == prepared.conversation.id).values(updated_at=func.now())
        )
        await self.session.commit()
        return message

    async def answer(self, prepared: PreparedChat) -> str:
        return await prepared.provider.generate(
            prompts.ANSWER_SYSTEM_PROMPT, prepared.messages, model=prepared.model
        )

    def stream(self, prepared: PreparedChat) -> AsyncIterator[str]:
        return prepared.provider.stream(prompts.ANSWER_SYSTEM_PROMPT, prepared.messages, model=prepared.model)


DEFAULT_SUGGESTIONS = [
    "What are the main concepts discussed?",
    "Explain the most important points in detail.",
    "What conclusions does the speaker reach?",
    "What are the key takeaways?",
]


async def generate_suggested_questions(
    session: AsyncSession, settings: Settings, video: Video, provider_name: str | None, force: bool = False
) -> list[str]:
    if video.suggested_questions and not force:
        return video.suggested_questions

    chunks = list(await ChunkRepository(session).list_for_video(video.id))
    if not chunks:
        return ["Summarize this video."] + DEFAULT_SUGGESTIONS

    budget, picked = 12000, []
    step = max(1, len(chunks) // max(1, budget // max(1, len(chunks[0].content))))
    for c in chunks[::step]:
        if budget - len(c.content) < 0:
            break
        picked.append(f"[{prompts.format_timestamp(c.start_time)}] {c.content}")
        budget -= len(c.content)

    questions = DEFAULT_SUGGESTIONS
    try:
        provider = get_llm_provider(provider_name, settings)
        raw = await provider.generate(
            prompts.SUGGEST_SYSTEM_PROMPT,
            [ChatMessage("user", f"Video title: {video.title}\n\nTranscript excerpts:\n" + "\n\n".join(picked))],
            json_mode=True,
        )
        generated = [str(q).strip() for q in _parse_json(raw).get("questions", []) if str(q).strip()]
        if generated:
            questions = generated[:4]
    except (AppError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Suggested question generation failed: %s", exc)
        # Don't cache the generic fallback, so a later request can try again.
        return ["Summarize this video."] + DEFAULT_SUGGESTIONS

    result = ["Summarize this video."] + questions
    await VideoRepository(session).update_fields(video.id, suggested_questions=result)
    await session.commit()
    return result
