"""Unit tests for single-flight duplicate request coalescing in ProfileService."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.cache import InMemoryCache
from app.extractor.mock import MockExtractor
from app.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_single_flight_coalesces_duplicate_concurrent_requests():
    mock_extractor = MockExtractor()
    fetch_spy = AsyncMock(wraps=mock_extractor.fetch)
    mock_extractor.fetch = fetch_spy

    cache = InMemoryCache(default_ttl_seconds=60)
    service = ProfileService(extractor=mock_extractor, cache=cache)

    # Launch 5 concurrent requests for the same uncached profile
    target_url = "https://www.linkedin.com/in/sarah-jenkins-dev"
    tasks = [service.lookup(target_url, request_id=f"req-{i}") for i in range(5)]

    results = await asyncio.gather(*tasks)

    # Verify all 5 callers received valid responses
    assert len(results) == 5
    for res in results:
        assert res.profile.full_name == "Sarah Jenkins"

    # Verify the underlying extractor fetch was only called EXACTLY ONCE
    assert fetch_spy.call_count == 1
