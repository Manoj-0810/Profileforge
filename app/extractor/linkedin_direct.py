"""Direct LinkedIn profile extractor implementing ProfileExtractor protocol."""

from __future__ import annotations

import structlog

from app.extractor.base import ProfileExtractor
from app.models import ProfileData, ProviderCapabilities
from app.providers.linkedin.client import LinkedInClient
from app.providers.linkedin.normalizer import LinkedInNormalizer
from app.providers.linkedin.parser import LinkedInParser
from app.providers.linkedin.resolver import LinkedInResolver
from app.services.url_utils import extract_slug_from_url

logger = structlog.get_logger(__name__)


class DirectLinkedInExtractor(ProfileExtractor):
    """Direct HTTP LinkedIn extractor using reverse-engineered Voyager endpoints."""

    def __init__(self, client: LinkedInClient) -> None:
        self.client = client
        self._capabilities = LinkedInNormalizer.get_capabilities()

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Declared extraction capabilities for direct LinkedIn HTTP provider."""
        return self._capabilities

    async def fetch(self, canonical_url: str) -> ProfileData:
        """Fetch and normalize profile data via direct HTTP communication.

        Args:
            canonical_url: Normalized canonical profile URL (e.g. 'https://www.linkedin.com/in/username').

        Returns:
            Fully populated and normalized ProfileData domain model.

        Raises:
            ProfileForgeError: Standardized error code on network, auth, or schema failures.
        """
        slug = extract_slug_from_url(canonical_url)
        logger.info("direct_extractor_fetch_start", slug=slug, url=canonical_url)

        # 1. Fetch raw normalized JSON from LinkedIn Voyager API
        raw_json = await self.client.fetch_profile_raw(slug)

        # 2. Parse raw response into structured intermediate entities
        parsed = LinkedInParser.parse(raw_json)

        # 3. Resolve foreign references, URN indices, and degree records
        resolved = LinkedInResolver.resolve(parsed)

        # 4. Normalize to domain model
        profile, _ = LinkedInNormalizer.normalize(
            resolved,
            canonical_url=canonical_url,
            parser_failed_sections=parsed.parser_failed_sections,
        )

        logger.info(
            "direct_extractor_fetch_success",
            slug=slug,
            full_name=profile.full_name,
            experiences=len(profile.experience),
            educations=len(profile.education),
            skills=len(profile.skills),
        )

        return profile
