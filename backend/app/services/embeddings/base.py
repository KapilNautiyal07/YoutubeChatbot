from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Produces vectors for documents and queries in the same embedding space."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Stable identifier stored alongside every vector, e.g. 'gemini:gemini-embedding-001@768'."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]: ...
