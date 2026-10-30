from collections.abc import AsyncIterator

from groq import AsyncGroq

from app.services.llm.base import ChatMessage, LLMProvider
from app.services.providers_common import map_groq_error

# Non-chat model families returned by the models endpoint.
_EXCLUDED = ("whisper", "tts", "guard", "playai", "orpheus", "distil", "prompt-guard", "compound")


class GroqProvider(LLMProvider):
    name = "groq"
    label = "Groq"

    def __init__(self, api_key: str, timeout_seconds: int = 90, **kwargs):
        super().__init__(**kwargs)
        self._client = AsyncGroq(api_key=api_key, max_retries=2, timeout=timeout_seconds)

    def _payload(self, system: str, messages: list[ChatMessage]) -> list[dict]:
        return [{"role": "system", "content": system}] + [{"role": m.role, "content": m.content} for m in messages]

    async def generate(self, system, messages, *, model=None, json_mode=False) -> str:
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        try:
            response = await self._client.chat.completions.create(
                model=model or self.default_model,
                messages=self._payload(system, messages),
                temperature=self.temperature,
                max_completion_tokens=self.max_output_tokens,
                **kwargs,
            )
        except Exception as exc:
            raise map_groq_error(exc) from exc
        return response.choices[0].message.content or ""

    async def stream(self, system, messages, *, model=None) -> AsyncIterator[str]:
        try:
            response = await self._client.chat.completions.create(
                model=model or self.default_model,
                messages=self._payload(system, messages),
                temperature=self.temperature,
                max_completion_tokens=self.max_output_tokens,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            raise map_groq_error(exc) from exc

    async def list_models(self) -> list[str]:
        try:
            result = await self._client.models.list()
        except Exception as exc:
            raise map_groq_error(exc) from exc
        ids = [m.id for m in result.data if getattr(m, "active", True)]
        return sorted(i for i in ids if not any(x in i.lower() for x in _EXCLUDED))
