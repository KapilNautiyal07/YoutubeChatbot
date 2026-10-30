from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings


def engine_options(settings: Settings) -> dict:
    options: dict = {"pool_pre_ping": True}
    if settings.database_uses_pooler:
        # Transaction-mode poolers can route statements to different server connections.
        options["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        }
    return options


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    **engine_options(settings),
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
