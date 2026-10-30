"""Shared helpers for translating provider SDK exceptions into safe application errors."""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.errors import ProviderAuthError, ProviderError, ProviderRateLimitError

logger = logging.getLogger(__name__)
T = TypeVar("T")


def map_gemini_error(exc: Exception) -> ProviderError:
    from google.genai import errors as genai_errors

    if isinstance(exc, genai_errors.APIError):
        message = (exc.message or "").lower()
        if exc.code in (401, 403) or "api key" in message or "api_key" in message:
            return ProviderAuthError("The Gemini API key is missing or invalid. Check GEMINI_API_KEY on the server.")
        if exc.code == 429:
            return ProviderRateLimitError("Gemini rate limit reached. Please wait a moment and try again.")
        if exc.code == 404:
            return ProviderError("The configured Gemini model was not found. Check the model name in settings.")
        if exc.code and exc.code >= 500:
            return ProviderError("Gemini is having trouble right now. Please try again shortly.")
        return ProviderError("Gemini rejected the request.")
    return ProviderError("Couldn't reach Gemini. Please check the server's network connection.")


def map_groq_error(exc: Exception) -> ProviderError:
    import groq

    if isinstance(exc, (groq.AuthenticationError, groq.PermissionDeniedError)):
        return ProviderAuthError("The Groq API key is missing or invalid. Check GROQ_API_KEY on the server.")
    if isinstance(exc, groq.RateLimitError):
        return ProviderRateLimitError(
            "Groq rate limit reached. Wait a moment, or switch to Gemini from the provider menu."
        )
    if isinstance(exc, groq.NotFoundError):
        return ProviderError("The selected Groq model is not available. Try another model.")
    if isinstance(exc, groq.BadRequestError):
        body = str(getattr(exc, "body", "") or "").lower()
        if "context" in body or "too large" in body or "tokens" in body:
            return ProviderRateLimitError(
                "The request was too large for this Groq model's limits. Try a shorter question or another model."
            )
        return ProviderError("Groq rejected the request.")
    if isinstance(exc, (groq.APIConnectionError, groq.APITimeoutError)):
        return ProviderError("Couldn't reach Groq. Please check the server's network connection.")
    return ProviderError("Groq is having trouble right now. Please try again shortly.")


async def with_retries(
    func: Callable[[], Awaitable[T]],
    *,
    is_retryable: Callable[[Exception], bool],
    attempts: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    label: str = "provider call",
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except Exception as exc:
            if attempt == attempts or not is_retryable(exc):
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1)) + random.uniform(0, 1)
            logger.warning("%s failed (%s); retry %d/%d in %.1fs", label, type(exc).__name__, attempt, attempts, delay)
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")


def gemini_retryable(exc: Exception) -> bool:
    from google.genai import errors as genai_errors

    if isinstance(exc, genai_errors.APIError):
        return exc.code == 429 or (exc.code or 0) >= 500
    # Timeouts are not retried: the request already waited the full timeout.
    return isinstance(exc, ConnectionError)
