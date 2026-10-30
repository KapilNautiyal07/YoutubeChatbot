"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    app_name: str = "Tubewise"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_chatbot"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Provider credentials (never sent to clients)
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # Chat model configuration
    llm_provider: str = "groq"
    groq_chat_model: str = "openai/gpt-oss-120b"
    gemini_chat_model: str = "gemini-3.5-flash"
    llm_temperature: float = 0.2
    llm_max_output_tokens: int = 4096
    llm_timeout_seconds: int = 90

    # Embedding configuration (kept separate from chat models for index compatibility)
    embedding_provider: str = "gemini"
    gemini_embedding_model: str = "gemini-embedding-001"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 768
    embedding_batch_size: int = 50

    # Chunking
    chunk_size: int = 1000  # characters
    chunk_overlap: int = 150  # characters

    # Retrieval
    top_k: int = 6
    similarity_threshold: float = 0.3
    rerank_enabled: bool = True
    candidate_pool_size: int = 20
    neighbor_window: int = 1
    max_context_chars: int = 24000
    history_messages: int = 8

    # Transcript handling
    preferred_languages: list[str] = Field(default_factory=lambda: ["en", "en-US", "en-GB"])
    max_transcript_chars: int = 1_500_000

    # Rate limiting (requests per minute per client IP)
    rate_limit_chat_per_minute: int = 20
    rate_limit_process_per_minute: int = 5

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        value = value.strip()
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                value = value.replace(prefix, "postgresql+asyncpg://", 1)
        # asyncpg uses `ssl` instead of libpq's `sslmode` and doesn't support `channel_binding`.
        parts = urlsplit(value)
        query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
        query = [("ssl", v) if k == "sslmode" else (k, v) for k, v in query]
        return urlunsplit(parts._replace(query=urlencode(query)))

    @property
    def database_uses_pooler(self) -> bool:
        """PgBouncer-style poolers (e.g. Neon '-pooler' hosts) need prepared-statement caching disabled."""
        return "-pooler" in (urlsplit(self.database_url).hostname or "")

    @field_validator("llm_provider", "embedding_provider")
    @classmethod
    def _lower(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def active_embedding_model(self) -> str:
        """Fully qualified identifier of the embedding model used for indexing and querying."""
        if self.embedding_provider == "local":
            return f"local:{self.local_embedding_model}"
        return f"gemini:{self.gemini_embedding_model}@{self.embedding_dimension}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
