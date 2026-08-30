"""Profile service coordinating validation, single-flight request coalescing, caching, and extraction."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog

from app.cache import CacheBackend, InMemoryCache
from app.extractor.base import ProfileExtractor
from app.models import (
    DataQuality,
    ProfileData,
    ProfileLookupResponse,
    ProviderCapabilities,
)
from app.services.url_utils import validate_and_canonicalize_url

logger = structlog.get_logger(__name__)


class ProfileService:
    """Core domain service for profile lookup."""

    def __init__(
        self,
        extractor: ProfileExtractor,
        cache: CacheBackend | None = None,
        max_concurrency: int = 2,
    ) -> None:
        self.extractor = extractor
        self.cache = cache or InMemoryCache()
        self.semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._in_flight: dict[str, asyncio.Future[ProfileData]] = {}
        self._in_flight_lock = asyncio.Lock()

    def _compute_data_quality(
        self, profile: ProfileData, capabilities: ProviderCapabilities
    ) -> DataQuality:
        """Construct objective data quality assessment from normalized ProfileData and capabilities."""
        available: list[str] = []

        if profile.full_name and profile.full_name != "N/A":
            available.append("full_name")
        if profile.headline:
            available.append("headline")
        if profile.location:
            available.append("location")
        if profile.about:
            available.append("about")
        if profile.experience:
            available.append("experience")
        if profile.education:
            available.append("education")
        if profile.skills:
            available.append("skills")
        if profile.certifications:
            available.append("certifications")
        if profile.languages:
            available.append("languages")
        if profile.profile_image_url:
            available.append("profile_image_url")

        supported = sorted(capabilities.supported_sections)
        missing = [s for s in supported if s not in available]
        unavailable = sorted(capabilities.unsupported_sections)

        score = round(len(available) / len(supported), 2) if supported else 0.0

        return DataQuality(
            available_sections=available,
            missing_sections=missing,
            unavailable_sections=unavailable,
            parser_failed_sections=[],
            completeness_score=score,
        )

    async def lookup(
        self,
        raw_url: str,
        request_id: str,
        override_extractor: ProfileExtractor | None = None,
        bypass_cache: bool = False,
    ) -> ProfileLookupResponse:
        """Coordinate profile lookup with validation, cache-aside, and request coalescing."""
        canonical_url, profile_id = validate_and_canonicalize_url(raw_url)
        active_extractor = override_extractor or self.extractor
        # Provider-scoped keys prevent a development mock response from being
        # served after switching to the live provider in the same process.
        cache_key = f"{active_extractor.capabilities.provider_name}:{profile_id}"

        # 1. Check cache (if not bypassed)
        if not bypass_cache:
            cached_profile = await self.cache.get(cache_key)
            if cached_profile is not None:
                logger.info(
                    "profile_cache_hit", profile_id=profile_id, request_id=request_id
                )
                dq = self._compute_data_quality(
                    cached_profile, active_extractor.capabilities
                )
                return ProfileLookupResponse(
                    profile=cached_profile,
                    fetched_at=datetime.now(timezone.utc),
                    cache_hit=True,
                    source=active_extractor.capabilities.provider_name,
                    request_id=request_id,
                    data_quality=dq,
                )

        # 2. Single-flight request coalescing
        async with self._in_flight_lock:
            if cache_key in self._in_flight:
                logger.info(
                    "profile_single_flight_coalesce",
                    profile_id=profile_id,
                    request_id=request_id,
                )
                future = self._in_flight[cache_key]
                wait_for_existing = True
            else:
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                self._in_flight[cache_key] = future
                wait_for_existing = False

        if wait_for_existing:
            # Await the primary worker's extraction
            profile = await future
            dq = self._compute_data_quality(profile, active_extractor.capabilities)
            return ProfileLookupResponse(
                profile=profile,
                fetched_at=datetime.now(timezone.utc),
                cache_hit=True,
                source=active_extractor.capabilities.provider_name,
                request_id=request_id,
                data_quality=dq,
            )

        # 3. Primary worker executes upstream extraction under concurrency guard
        try:
            logger.info(
                "profile_upstream_fetch_start",
                profile_id=profile_id,
                request_id=request_id,
                provider=active_extractor.capabilities.provider_name,
            )
            async with self.semaphore:
                profile = await active_extractor.fetch(canonical_url)

            # Store in cache
            await self.cache.set(cache_key, profile)

            # Resolve future for all concurrent waiters
            if not future.done():
                future.set_result(profile)

            dq = self._compute_data_quality(profile, active_extractor.capabilities)
            return ProfileLookupResponse(
                profile=profile,
                fetched_at=datetime.now(timezone.utc),
                cache_hit=False,
                source=active_extractor.capabilities.provider_name,
                request_id=request_id,
                data_quality=dq,
            )

        except Exception as exc:
            if not future.done():
                future.set_exception(exc)
                if not future.cancelled():
                    # Consume exception to avoid asyncio unretrieved exception warnings
                    future.exception()
            raise

        finally:
            async with self._in_flight_lock:
                self._in_flight.pop(cache_key, None)
