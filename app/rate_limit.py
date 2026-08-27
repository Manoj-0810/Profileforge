"""Sliding window rate limiter per API key."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import Depends

from app.auth import verify_api_key
from app.config import settings
from app.errors import ErrorCode, ProfileForgeError


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - self.window_seconds

        async with self._lock:
            timestamps = self._history.setdefault(key, [])
            # Filter expired timestamps
            valid_timestamps = [ts for ts in timestamps if ts > cutoff]
            self._history[key] = valid_timestamps

            if len(valid_timestamps) >= self.max_requests:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                raise ProfileForgeError(
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s). Retry in {retry_after}s.",
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )

            valid_timestamps.append(now)

    async def reset(self) -> None:
        async with self._lock:
            self._history.clear()


# Global limiter instance
rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


async def rate_limit_dependency(api_key: str = Depends(verify_api_key)) -> str:
    """FastAPI dependency enforcing rate limits on authenticated API keys."""
    await rate_limiter.check(api_key)
    return api_key
