import logging
import math

from google import genai
from google.genai import types

from app.services.embeddings.base import EmbeddingProvider
from app.services.providers_common import gemini_retryable, map_gemini_error, with_retries

logger = logging.getLogger(__name__)

# The Gemini batch embedding endpoint accepts at most 100 inputs per request.
_MAX_BATCH = 100


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dimension: int, batch_size: int = 50):
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=120_000))
        self._model = model
        self._dimension = dimension
        self._batch_size = max(1, min(batch_size, _MAX_BATCH))

    @property
    def model_id(self) -> str:
        return f"gemini:{self._model}@{self._dimension}"

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=self._dimension)

        async def call():
            return await self._client.aio.models.embed_content(model=self._model, contents=texts, config=config)

        try:
            response = await with_retries(call, is_retryable=gemini_retryable, label="Gemini embedding")
        except Exception as exc:
            raise map_gemini_error(exc) from exc
        # Truncated (non-default) dimensions are not unit-length; normalize for cosine search.
        return [_normalize(list(e.values)) for e in response.embeddings]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(await self._embed(batch, "RETRIEVAL_DOCUMENT"))
            logger.debug("Embedded %d/%d chunks", len(vectors), len(texts))
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], "RETRIEVAL_QUERY"))[0]
