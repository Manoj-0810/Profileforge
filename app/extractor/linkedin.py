"""LinkedIn extractor implementation using the LinkedAPI provider adapter."""

from __future__ import annotations

from app.extractor.base import ProfileExtractor
from app.models import ProfileData, ProviderCapabilities
from app.providers.linkedapi.client import LinkedAPIClient
from app.providers.linkedapi.normalizer import (
    LinkedAPINormalizer,
)
from app.providers.linkedapi.parser import LinkedAPIParser


class LinkedInExtractor(ProfileExtractor):
    """Adapter encapsulating LinkedAPI workflow submission, parsing, and normalization."""

    def __init__(
        self,
        client: LinkedAPIClient | None = None,
        parser: LinkedAPIParser | None = None,
        normalizer: LinkedAPINormalizer | None = None,
    ) -> None:
        self.client = client or LinkedAPIClient()
        self.parser = parser or LinkedAPIParser()
        self.normalizer = normalizer or LinkedAPINormalizer()

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.normalizer.capabilities

    async def fetch(self, canonical_url: str) -> ProfileData:
        """Fetch, parse, resolve, and normalize profile for canonical LinkedIn URL."""
        completion_payload = await self.client.execute_profile_workflow(canonical_url)
        parsed_raw = self.parser.parse(completion_payload)
        profile_data = self.normalizer.normalize(parsed_raw, canonical_url)
        return profile_data
