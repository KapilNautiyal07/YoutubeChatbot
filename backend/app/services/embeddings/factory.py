from app.core.config import Settings, get_settings
from app.core.errors import EmbeddingMismatchError, ProviderNotConfiguredError
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.gemini import GeminiEmbeddingProvider
from app.services.embeddings.local import LocalEmbeddingProvider


def _build(model_id: str, settings: Settings) -> EmbeddingProvider:
    kind, _, spec = model_id.partition(":")
    if kind == "gemini":
        if not settings.gemini_api_key:
            raise ProviderNotConfiguredError("GEMINI_API_KEY is not set, so Gemini embeddings are unavailable.")
        model, _, dim = spec.partition("@")
        return GeminiEmbeddingProvider(
            settings.gemini_api_key, model, int(dim or settings.embedding_dimension), settings.embedding_batch_size
        )
    if kind == "local":
        return LocalEmbeddingProvider(spec)
    raise EmbeddingMismatchError(f"Unknown embedding model '{model_id}'. Re-index this video.")


def get_indexing_embedder(settings: Settings | None = None) -> EmbeddingProvider:
    """Embedder used for new indexing jobs, from current configuration."""
    settings = settings or get_settings()
    return _build(settings.active_embedding_model, settings)


def get_embedder_for(model_id: str, settings: Settings | None = None) -> EmbeddingProvider:
    """Embedder matching the model a video was indexed with, so query vectors are compatible."""
    return _build(model_id, settings or get_settings())
