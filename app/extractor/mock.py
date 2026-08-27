"""Mock extractor implementation for deterministic offline testing and local development."""

from __future__ import annotations

import json
from pathlib import Path

from app.errors import ErrorCode, ProfileForgeError
from app.extractor.base import ProfileExtractor
from app.models import ProfileData, ProviderCapabilities
from app.providers.linkedapi.normalizer import (
    LINKEDAPI_CAPABILITIES,
    LinkedAPINormalizer,
)
from app.providers.linkedapi.parser import LinkedAPIParser


class MockExtractor(ProfileExtractor):
    """Deterministic, offline extractor returning fixture-backed profiles."""

    def __init__(
        self,
        fixtures_dir: Path | None = None,
        parser: LinkedAPIParser | None = None,
        normalizer: LinkedAPINormalizer | None = None,
    ) -> None:
        self.fixtures_dir = fixtures_dir or (
            Path(__file__).parent.parent.parent / "tests" / "fixtures" / "raw_upstream"
        )
        self.parser = parser or LinkedAPIParser()
        self.normalizer = normalizer or LinkedAPINormalizer()

    @property
    def capabilities(self) -> ProviderCapabilities:
        return LINKEDAPI_CAPABILITIES

    def _load_fixture(self, filename: str) -> dict:
        fixture_path = self.fixtures_dir / filename
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture {filename} not found at {fixture_path}")
        with open(fixture_path, encoding="utf-8") as f:
            return json.load(f)

    async def fetch(self, canonical_url: str) -> ProfileData:
        """Return deterministic ProfileData based on slug in canonical_url."""
        slug = canonical_url.rstrip("/").split("/")[-1].lower()

        if "not-found" in slug or "nonexistent" in slug:
            raise ProfileForgeError(
                ErrorCode.PROFILE_NOT_FOUND,
                f"Profile '{slug}' not found on LinkedIn",
                status_code=404,
            )

        if "auth-fail" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_AUTH_FAILED,
                "LinkedIn account disconnected or signed out",
                status_code=502,
            )

        if "rate-limit" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_RATE_LIMITED,
                "Upstream rate limit exceeded for account",
                status_code=502,
            )

        if "timeout" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_TIMEOUT,
                "Upstream profile lookup timed out after 120.0s",
                status_code=504,
            )

        if "schema-drift" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Upstream schema structurally altered",
                status_code=502,
            )

        if "alex-mercer" in slug or "partial" in slug:
            raw_data = self._load_fixture("partial_profile.json")
        elif "missing-image" in slug or "elena-rostova" in slug:
            raw_data = self._load_fixture("missing_image.json")
        elif "missing-about" in slug or "marcus-vance" in slug:
            raw_data = self._load_fixture("missing_about.json")
        elif "languages" in slug or "jean-luc" in slug:
            raw_data = self._load_fixture("languages_response.json")
        elif "skills-only" in slug or "maya-lin" in slug:
            raw_data = self._load_fixture("skills_only.json")
        elif "localized" in slug or "tanaka" in slug:
            raw_data = self._load_fixture("localized_profile.json")
        else:
            raw_data = self._load_fixture("complete_profile.json")

        parsed = self.parser.parse(raw_data)
        return self.normalizer.normalize(parsed, canonical_url)
