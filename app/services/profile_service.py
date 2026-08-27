"""Profile service coordinating validation, single-flight request coalescing, caching, and extraction."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog

from app.cache import CacheBackend, InMemoryCache
from app.extractor.base import ProfileExtractor
from app.models import ProfileData, ProfileLookupResponse
from app.providers.linkedapi.normalizer import LinkedAPINormalizer
from app.providers.linkedapi.parser import ParsedRawProfile
from app.services.url_utils import validate_and_canonicalize_url

logger = structlog.get_logger(__name__)


class ProfileService:
    """Core domain service for profile lookup."""

    def __init__(
        self,
        extractor: ProfileExtractor,
        cache: CacheBackend | None = None,
        max_concurrency: int = 2,
        normalizer: LinkedAPINormalizer | None = None,
    ) -> None:
        self.extractor = extractor
        self.cache = cache or InMemoryCache()
        self.semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self.normalizer = normalizer or LinkedAPINormalizer(
            capabilities=extractor.capabilities
        )
        self._in_flight: dict[str, asyncio.Future[ProfileData]] = {}
        self._in_flight_lock = asyncio.Lock()

    def _build_data_quality_from_profile(self, profile: ProfileData):
        """Construct data quality assessment from normalized ProfileData."""
        parsed_repr = ParsedRawProfile(
            name=profile.full_name,
            headline=profile.headline,
            location=profile.location,
            country_code=profile.country_code,
            about=profile.about,
            profile_image_url=profile.profile_image_url,
            public_url=profile.profile_url,
            urn=profile.urn,
            skills_list=profile.skills,
        )
        return self.normalizer.compute_data_quality(
            parsed=parsed_repr,
            experiences_count=len(profile.experience),
            educations_count=len(profile.education),
            languages_count=len(profile.languages),
        )

    async def lookup(self, raw_url: str, request_id: str) -> ProfileLookupResponse:
        """Coordinate profile lookup with validation, cache-aside, and request coalescing."""
        canonical_url, profile_id = validate_and_canonicalize_url(raw_url)

        # 1. Check cache
        cached_profile = await self.cache.get(profile_id)
        if cached_profile is not None:
            logger.info(
                "profile_cache_hit", profile_id=profile_id, request_id=request_id
            )
            dq = self._build_data_quality_from_profile(cached_profile)
            return ProfileLookupResponse(
                profile=cached_profile,
                fetched_at=datetime.now(timezone.utc),
                cache_hit=True,
                source=self.extractor.capabilities.provider_name,
                request_id=request_id,
                data_quality=dq,
            )

        # 2. Single-flight request coalescing
        async with self._in_flight_lock:
            if profile_id in self._in_flight:
                logger.info(
                    "profile_single_flight_coalesce",
                    profile_id=profile_id,
                    request_id=request_id,
                )
                future = self._in_flight[profile_id]
                wait_for_existing = True
            else:
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                self._in_flight[profile_id] = future
                wait_for_existing = False

        if wait_for_existing:
            # Await the primary worker's extraction
            profile = await future
            dq = self._build_data_quality_from_profile(profile)
            return ProfileLookupResponse(
                profile=profile,
                fetched_at=datetime.now(timezone.utc),
                cache_hit=True,
                source=self.extractor.capabilities.provider_name,
                request_id=request_id,
                data_quality=dq,
            )

        # 3. Primary worker executes upstream extraction under concurrency guard
        try:
            logger.info(
                "profile_upstream_fetch_start",
                profile_id=profile_id,
                request_id=request_id,
            )
            async with self.semaphore:
                profile = await self.extractor.fetch(canonical_url)

            # Store in cache
            await self.cache.set(profile_id, profile)

            # Resolve future for all concurrent waiters
            if not future.done():
                future.set_result(profile)

            dq = self._build_data_quality_from_profile(profile)
            return ProfileLookupResponse(
                profile=profile,
                fetched_at=datetime.now(timezone.utc),
                cache_hit=False,
                source=self.extractor.capabilities.provider_name,
                request_id=request_id,
                data_quality=dq,
            )

        except Exception as exc:
            if not future.done():
                future.set_exception(exc)
            raise

        finally:
            async with self._in_flight_lock:
                self._in_flight.pop(profile_id, None)
