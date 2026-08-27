"""Unit tests for sliding window rate limiter and Retry-After headers."""

from __future__ import annotations

import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.rate_limit import SlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_quota():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10)
    # 3 requests should pass
    await limiter.check("key-1")
    await limiter.check("key-1")
    await limiter.check("key-1")


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_quota():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10)
    await limiter.check("key-1")
    await limiter.check("key-1")

    with pytest.raises(ProfileForgeError) as exc_info:
        await limiter.check("key-1")

    assert exc_info.value.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) >= 1


@pytest.mark.asyncio
async def test_rate_limiter_different_keys_isolated():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=10)
    await limiter.check("key-A")

    # key-B should still be allowed
    await limiter.check("key-B")

    # key-A should be blocked
    with pytest.raises(ProfileForgeError):
        await limiter.check("key-A")
