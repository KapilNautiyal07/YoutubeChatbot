from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from app.services.llm.base import ChatMessage, LLMProvider
from app.services.providers_common import gemini_retryable, map_gemini_error, with_retries

_EXCLUDED = (
    "embedding", "tts", "image", "audio", "live", "aqa", "robotics", "computer-use", "veo", "imagen", "banana",
    "transcribe", "customtools",
)


class GeminiProvider(LLMProvider):
    name = "gemini"
    label = "Google Gemini"

    def __init__(self, api_key: str, timeout_seconds: int = 90, **kwargs):
        super().__init__(**kwargs)
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_seconds * 1000))

    @staticmethod
    def _contents(messages: list[ChatMessage]) -> list[types.Content]:
        return [
            types.Content(role="model" if m.role == "assistant" else "user", parts=[types.Part(text=m.content)])
            for m in messages
        ]

    def _config(self, system: str, json_mode: bool = False) -> types.GenerateContentConfig:
        # Output budget is left to the model default: thinking models spend part of the
        # output budget on reasoning, and a tight cap can truncate the visible answer.
        return types.GenerateContentConfig(
            system_instruction=system,
            temperature=self.temperature,
            response_mime_type="application/json" if json_mode else None,
        )

    async def generate(self, system, messages, *, model=None, json_mode=False) -> str:
        async def call():
            return await self._client.aio.models.generate_content(
                model=model or self.default_model,
                contents=self._contents(messages),
                config=self._config(system, json_mode),
            )

        try:
            response = await with_retries(call, is_retryable=gemini_retryable, attempts=3, label="Gemini chat")
        except Exception as exc:
            raise map_gemini_error(exc) from exc
        return response.text or ""

    async def stream(self, system, messages, *, model=None) -> AsyncIterator[str]:
        try:
            response = await self._client.aio.models.generate_content_stream(
                model=model or self.default_model,
                contents=self._contents(messages),
                config=self._config(system),
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            raise map_gemini_error(exc) from exc

    async def list_models(self) -> list[str]:
        models: list[str] = []
        try:
            pager = await self._client.aio.models.list()
            async for m in pager:
                name = (m.name or "").removeprefix("models/")
                actions = m.supported_actions or []
                if "generateContent" in actions and name.startswith("gemini") and not any(x in name for x in _EXCLUDED):
                    models.append(name)
        except Exception as exc:
            raise map_gemini_error(exc) from exc
        return sorted(models, reverse=True)
