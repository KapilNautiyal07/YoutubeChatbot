"""Simple in-memory sliding-window rate limiter keyed by client IP.

Suitable for a single-process deployment. For multiple workers, back this with Redis.
"""

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.errors import RateLimitExceededError


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            retry_in = int(self.window - (now - hits[0])) + 1
            raise RateLimitExceededError(f"Too many requests. Please try again in {retry_in} seconds.")
        hits.append(now)


def limiter_dependency(limiter: RateLimiter):
    async def _dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        limiter.check(client)

    return _dependency
