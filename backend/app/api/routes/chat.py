import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import chat_rate_limit, message_to_out
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import SessionLocal, get_session
from app.schemas import ChatRequest, ChatResponse
from app.services.rag.pipeline import RAGPipeline, serialize_sources

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(chat_rate_limit)])


async def _prepare(payload: ChatRequest, session: AsyncSession):
    pipeline = RAGPipeline(session, get_settings())
    prepared = await pipeline.prepare(
        video_id=payload.video_id,
        conversation_id=payload.conversation_id,
        question=payload.question.strip(),
        provider_name=payload.provider,
        model=payload.model,
    )
    return pipeline, prepared


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, session: AsyncSession = Depends(get_session)):
    pipeline, prepared = await _prepare(payload, session)
    answer = await pipeline.answer(prepared)
    message = await pipeline.save_answer(prepared, answer)
    return ChatResponse(
        conversation_id=prepared.conversation.id,
        user_message_id=prepared.user_message_id,
        message=message_to_out(message),
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/stream")
async def chat_stream(payload: ChatRequest, session: AsyncSession = Depends(get_session)):
    """Server-sent events: `meta` (sources), many `token`, then `done` or `error`."""
    # Retrieval runs before the stream opens so setup errors return proper HTTP status codes.
    pipeline, prepared = await _prepare(payload, session)
    sources = [s for s in serialize_sources(prepared.chunks) if s["source"] == "match"]
    sources.sort(key=lambda s: s["start_time"])

    async def events():
        yield _sse("meta", {
            "conversation_id": prepared.conversation.id,
            "user_message_id": prepared.user_message_id,
            "provider": prepared.provider.name,
            "model": prepared.model,
            "sources": sources,
        })
        parts: list[str] = []
        try:
            async for token in pipeline.stream(prepared):
                parts.append(token)
                yield _sse("token", {"text": token})
            answer = "".join(parts).strip() or "I couldn't generate an answer this time. Please try again."
            async with SessionLocal() as save_session:
                message = await RAGPipeline(save_session, get_settings()).save_answer(prepared, answer)
            yield _sse("done", {"message": message_to_out(message).model_dump(mode="json")})
        except AppError as exc:
            yield _sse("error", {"code": exc.code, "message": exc.message})
        except Exception:
            logger.exception("Streaming answer failed")
            yield _sse("error", {"code": "internal_error", "message": "Something went wrong while answering."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
