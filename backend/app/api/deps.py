from app.core.config import get_settings
from app.core.rate_limit import RateLimiter, limiter_dependency
from app.db.models import Message
from app.schemas import MessageOut, SourceOut

_settings = get_settings()

chat_rate_limit = limiter_dependency(RateLimiter(_settings.rate_limit_chat_per_minute))
process_rate_limit = limiter_dependency(RateLimiter(_settings.rate_limit_process_per_minute))


def message_to_out(message: Message) -> MessageOut:
    sources = [
        SourceOut(**{k: s[k] for k in ("chunk_index", "start_time", "end_time", "score", "content")})
        for s in (message.retrieved_chunks or [])
        if s.get("source") == "match"
    ]
    sources.sort(key=lambda s: s.start_time)
    return MessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        provider=message.provider,
        model=message.model,
        sources=sources,
        created_at=message.created_at,
    )
