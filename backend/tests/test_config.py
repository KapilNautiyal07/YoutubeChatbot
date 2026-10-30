from app.core.config import Settings


def test_libpq_url_is_converted_for_asyncpg():
    s = Settings(
        _env_file=None,
        database_url="postgresql://u:p@ep-x-pooler.region.aws.neon.tech/db?sslmode=require&channel_binding=require",
    )
    assert s.database_url == "postgresql+asyncpg://u:p@ep-x-pooler.region.aws.neon.tech/db?ssl=require"
    assert s.database_uses_pooler


def test_local_url_untouched():
    s = Settings(_env_file=None, database_url="postgresql+asyncpg://postgres:pw@localhost:5432/youtube_chatbot")
    assert s.database_url == "postgresql+asyncpg://postgres:pw@localhost:5432/youtube_chatbot"
    assert not s.database_uses_pooler


def test_embedding_model_id_includes_dimension():
    s = Settings(_env_file=None, embedding_provider="gemini", gemini_embedding_model="gemini-embedding-001",
                 embedding_dimension=768)
    assert s.active_embedding_model == "gemini:gemini-embedding-001@768"
