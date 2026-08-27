"""In-memory cache backend with TTL and canonical profile ID keying."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from app.models import ProfileData


@runtime_checkable
class CacheBackend(Protocol):
    """Cache storage protocol for ProfileForge."""

    async def get(self, key: str) -> ProfileData | None:
        """Retrieve cached ProfileData if present and unexpired."""
        ...

    async def set(self, key: str, value: ProfileData, ttl_seconds: int = 3600) -> None:
        """Store ProfileData with expiration TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Evict key from cache."""
        ...

    async def clear(self) -> None:
        """Clear all entries."""
        ...


class _CacheEntry:
    def __init__(self, value: ProfileData, expires_at: datetime | None) -> None:
        self.value = value
        self.expires_at = expires_at

    def is_expired(self, now: datetime) -> bool:
        if self.expires_at is None:
            return False
        return now >= self.expires_at


class InMemoryCache(CacheBackend):
    """In-memory thread-safe dictionary cache with TTL expiration and hit/miss tracking."""

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.hits: int = 0
        self.misses: int = 0

    async def get(self, key: str) -> ProfileData | None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None

            if entry.is_expired(now):
                del self._store[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry.value

    async def set(
        self, key: str, value: ProfileData, ttl_seconds: int | None = None
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        now = datetime.now(timezone.utc)
        expires_at = (
            datetime.fromtimestamp(now.timestamp() + ttl, tz=timezone.utc)
            if ttl > 0
            else None
        )

        async with self._lock:
            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0

    async def get_stats(self) -> dict[str, int]:
        async with self._lock:
            return {
                "size": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
            }
