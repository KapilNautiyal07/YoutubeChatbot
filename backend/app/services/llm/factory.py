"""Registry of chat providers. Add a provider by implementing LLMProvider and registering a builder."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.errors import ProviderError, ProviderNotConfiguredError
from app.services.llm.base import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider

logger = logging.getLogger(__name__)


@dataclass
class ProviderSpec:
    name: str
    label: str
    description: str
    api_key: Callable[[Settings], str]
    default_model: Callable[[Settings], str]
    builder: Callable[[Settings], LLMProvider]


def _common(settings: Settings) -> dict:
    return {
        "temperature": settings.llm_temperature,
        "max_output_tokens": settings.llm_max_output_tokens,
        "timeout_seconds": settings.llm_timeout_seconds,
    }


PROVIDERS: dict[str, ProviderSpec] = {
    "groq": ProviderSpec(
        name="groq",
        label="Groq",
        description="Very fast open-weight models",
        api_key=lambda s: s.groq_api_key,
        default_model=lambda s: s.groq_chat_model,
        builder=lambda s: GroqProvider(s.groq_api_key, default_model=s.groq_chat_model, **_common(s)),
    ),
    "gemini": ProviderSpec(
        name="gemini",
        label="Google Gemini",
        description="Long-context models from Google",
        api_key=lambda s: s.gemini_api_key,
        default_model=lambda s: s.gemini_chat_model,
        builder=lambda s: GeminiProvider(s.gemini_api_key, default_model=s.gemini_chat_model, **_common(s)),
    ),
}

_instances: dict[str, LLMProvider] = {}
_model_cache: dict[str, tuple[float, list[str]]] = {}
_MODEL_CACHE_TTL = 600


def get_llm_provider(name: str | None = None, settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    key = (name or settings.llm_provider).lower()
    spec = PROVIDERS.get(key)
    if spec is None:
        raise ProviderNotConfiguredError(f"Unknown provider '{key}'. Choose one of: {', '.join(PROVIDERS)}.")
    if not spec.api_key(settings):
        raise ProviderNotConfiguredError(f"{spec.label} isn't configured on the server (missing API key).")
    if key not in _instances:
        _instances[key] = spec.builder(settings)
    return _instances[key]


async def list_provider_models(name: str, settings: Settings | None = None) -> tuple[list[str], str]:
    """Return (available chat models, effective default model) for a provider."""
    settings = settings or get_settings()
    configured = PROVIDERS[name].default_model(settings)
    cached = _model_cache.get(name)
    if cached and time.monotonic() - cached[0] < _MODEL_CACHE_TTL:
        models = cached[1]
    else:
        try:
            models = await get_llm_provider(name, settings).list_models()
        except ProviderError as exc:
            logger.warning("Could not list %s models: %s", name, exc.message)
            return [configured], configured
        _model_cache[name] = (time.monotonic(), models)
    if not models:
        return [configured], configured
    if configured in models:
        return models, configured
    logger.warning("Configured %s model '%s' is not available to this API key; using '%s'.", name, configured, models[0])
    return models, models[0]
