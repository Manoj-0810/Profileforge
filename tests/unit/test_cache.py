"""Unit tests for InMemoryCache TTL expiration and statistics."""

from __future__ import annotations

import asyncio

import pytest

from app.cache import InMemoryCache
from app.models import ProfileData


@pytest.fixture
def sample_profile() -> ProfileData:
    return ProfileData(
        full_name="Bob Test",
        profile_url="https://www.linkedin.com/in/bob-test",
        canonical_url="https://www.linkedin.com/in/bob-test",
    )


@pytest.mark.asyncio
async def test_cache_miss_and_hit(sample_profile: ProfileData):
    cache = InMemoryCache(default_ttl_seconds=60)

    # Cache MISS
    val = await cache.get("bob-test")
    assert val is None
    assert cache.misses == 1
    assert cache.hits == 0

    # Cache SET
    await cache.set("bob-test", sample_profile)

    # Cache HIT
    val = await cache.get("bob-test")
    assert val is not None
    assert val.full_name == "Bob Test"
    assert cache.hits == 1


@pytest.mark.asyncio
async def test_cache_ttl_expiration(sample_profile: ProfileData):
    # Set short TTL
    cache = InMemoryCache(default_ttl_seconds=0)  # 0 or 1s
    await cache.set("bob-test", sample_profile, ttl_seconds=1)

    # Immediate hit
    val = await cache.get("bob-test")
    assert val is not None

    # Wait for expiration
    await asyncio.sleep(1.1)

    val_after = await cache.get("bob-test")
    assert val_after is None
    assert cache.misses >= 1


@pytest.mark.asyncio
async def test_cache_delete_and_clear(sample_profile: ProfileData):
    cache = InMemoryCache(default_ttl_seconds=60)
    await cache.set("user1", sample_profile)
    await cache.set("user2", sample_profile)

    stats = await cache.get_stats()
    assert stats["size"] == 2

    await cache.delete("user1")
    assert await cache.get("user1") is None
    assert await cache.get("user2") is not None

    await cache.clear()
    stats_after = await cache.get_stats()
    assert stats_after["size"] == 0
