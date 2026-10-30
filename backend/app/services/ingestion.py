"""Background ingestion: metadata -> transcript -> chunks -> embeddings -> PostgreSQL."""

import asyncio
import logging
import uuid

from app.core.config import get_settings
from app.core.errors import AppError, TranscriptError
from app.db.models import TranscriptChunk, VideoStatus
from app.db.repositories import ChunkRepository, VideoRepository
from app.db.session import SessionLocal
from app.services.embeddings.factory import get_indexing_embedder
from app.services.processing.chunker import chunk_segments
from app.services.youtube.metadata import fetch_metadata
from app.services.youtube.transcript import fetch_transcript

logger = logging.getLogger(__name__)

_running: dict[uuid.UUID, asyncio.Task] = {}

IN_PROGRESS = {VideoStatus.PENDING.value, VideoStatus.FETCHING_TRANSCRIPT.value, VideoStatus.EMBEDDING.value}


def is_running(video_id: uuid.UUID) -> bool:
    task = _running.get(video_id)
    return task is not None and not task.done()


def cancel(video_id: uuid.UUID) -> None:
    task = _running.pop(video_id, None)
    if task and not task.done():
        task.cancel()


def schedule_ingestion(video_id: uuid.UUID, youtube_video_id: str, language: str | None) -> None:
    if is_running(video_id):
        return
    task = asyncio.create_task(_ingest(video_id, youtube_video_id, language), name=f"ingest-{youtube_video_id}")
    _running[video_id] = task
    task.add_done_callback(lambda _: _running.pop(video_id, None))


async def _set_status(video_id: uuid.UUID, status: VideoStatus, message: str | None = None, **fields) -> None:
    async with SessionLocal() as session:
        await VideoRepository(session).update_fields(
            video_id, status=status.value, status_message=message, **fields
        )
        await session.commit()


async def _ingest(video_id: uuid.UUID, youtube_video_id: str, language: str | None) -> None:
    settings = get_settings()
    log_ctx = f"[{youtube_video_id}]"
    try:
        await _set_status(video_id, VideoStatus.FETCHING_TRANSCRIPT, "Looking up the video…", error_message=None)
        meta = await fetch_metadata(youtube_video_id)
        await _set_status(
            video_id,
            VideoStatus.FETCHING_TRANSCRIPT,
            "Reading the transcript…",
            title=meta.title,
            channel_name=meta.channel_name,
            thumbnail_url=meta.thumbnail_url,
            duration=meta.duration,
        )

        transcript = await fetch_transcript(
            youtube_video_id, requested_language=language, preferred=settings.preferred_languages
        )
        total_chars = sum(len(s.text) for s in transcript.segments)
        if total_chars > settings.max_transcript_chars:
            raise TranscriptError(
                f"This transcript is very long ({total_chars:,} characters). The current limit is "
                f"{settings.max_transcript_chars:,}; raise MAX_TRANSCRIPT_CHARS to allow it.",
                code="transcript_too_long",
            )

        chunks = chunk_segments(transcript.segments, settings.chunk_size, settings.chunk_overlap)
        logger.info("%s %d segments -> %d chunks (%s)", log_ctx, len(transcript.segments), len(chunks),
                    transcript.language_code)

        embedder = get_indexing_embedder(settings)
        vectors: list[list[float]] = []
        batch = settings.embedding_batch_size
        for start in range(0, len(chunks), batch):
            await _set_status(
                video_id, VideoStatus.EMBEDDING, f"Understanding the content… {start}/{len(chunks)} sections"
            )
            vectors.extend(await embedder.embed_documents([c.content for c in chunks[start : start + batch]]))

        duration = meta.duration or int(max(c.end_time for c in chunks))
        async with SessionLocal() as session:
            rows = [
                TranscriptChunk(
                    video_id=video_id,
                    chunk_index=c.index,
                    content=c.content,
                    start_time=c.start_time,
                    end_time=c.end_time,
                    embedding=v,
                    embedding_model=embedder.model_id,
                )
                for c, v in zip(chunks, vectors, strict=True)
            ]
            await ChunkRepository(session).replace_for_video(video_id, rows)
            await VideoRepository(session).update_fields(
                video_id,
                status=VideoStatus.READY.value,
                status_message=None,
                error_message=None,
                duration=duration,
                transcript_language=transcript.language,
                transcript_language_code=transcript.language_code,
                transcript_is_generated=transcript.is_generated,
                transcript_is_translated=transcript.is_translated,
                embedding_model=embedder.model_id,
                chunk_count=len(rows),
                transcript_chars=total_chars,
                suggested_questions=None,
            )
            await session.commit()
        logger.info("%s ready with %d chunks using %s", log_ctx, len(chunks), embedder.model_id)

    except AppError as exc:
        logger.warning("%s ingestion failed: %s", log_ctx, exc.message)
        await _safe_fail(video_id, exc.message)
    except Exception:
        logger.exception("%s unexpected ingestion failure", log_ctx)
        await _safe_fail(video_id, "Something went wrong while processing this video. Please try again.")


async def _safe_fail(video_id: uuid.UUID, message: str) -> None:
    try:
        await _set_status(video_id, VideoStatus.FAILED, None, error_message=message)
    except Exception:
        logger.exception("Could not record failure for video %s", video_id)
