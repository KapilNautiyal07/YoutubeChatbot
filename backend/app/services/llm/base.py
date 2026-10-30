from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    """Chat-completion provider. Implementations must not leak credentials in errors."""

    name: str
    label: str

    def __init__(self, default_model: str, temperature: float, max_output_tokens: int):
        self.default_model = default_model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    @abstractmethod
    async def generate(
        self, system: str, messages: list[ChatMessage], *, model: str | None = None, json_mode: bool = False
    ) -> str: ...

    @abstractmethod
    def stream(self, system: str, messages: list[ChatMessage], *, model: str | None = None) -> AsyncIterator[str]: ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Chat models currently available to the configured account."""
