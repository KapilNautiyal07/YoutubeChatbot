"""Optional on-device embeddings via fastembed (ONNX). Install with requirements-local.txt."""

import asyncio
from functools import lru_cache

from app.core.errors import ProviderNotConfiguredError
from app.services.embeddings.base import EmbeddingProvider


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise ProviderNotConfiguredError(
            "Local embeddings require the 'fastembed' package. Install backend/requirements-local.txt."
        ) from exc
    return TextEmbedding(model_name=model_name)


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str):
        self._model_name = model

    @property
    def model_id(self) -> str:
        return f"local:{self._model_name}"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        def run():
            model = _load_model(self._model_name)
            return [v.tolist() for v in model.passage_embed(texts)]

        return await asyncio.to_thread(run)

    async def embed_query(self, text: str) -> list[float]:
        def run():
            model = _load_model(self._model_name)
            return next(iter(model.query_embed(text))).tolist()

        return await asyncio.to_thread(run)
