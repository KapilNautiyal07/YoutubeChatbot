"""Domain errors carrying a safe, user-facing message and an HTTP status code."""


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class InvalidURLError(AppError):
    status_code = 422
    code = "invalid_url"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class TranscriptError(AppError):
    status_code = 422
    code = "transcript_unavailable"


class VideoUnavailableError(AppError):
    status_code = 404
    code = "video_unavailable"


class ProviderError(AppError):
    """Failure talking to an LLM or embedding provider."""

    status_code = 502
    code = "provider_error"


class ProviderAuthError(ProviderError):
    status_code = 502
    code = "provider_auth_error"


class ProviderRateLimitError(ProviderError):
    status_code = 429
    code = "provider_rate_limited"


class ProviderNotConfiguredError(ProviderError):
    status_code = 400
    code = "provider_not_configured"


class EmbeddingMismatchError(AppError):
    status_code = 409
    code = "embedding_mismatch"


class RateLimitExceededError(AppError):
    status_code = 429
    code = "rate_limited"
