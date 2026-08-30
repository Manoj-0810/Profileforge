"""Domain normalization and objective DataQuality calculation for direct LinkedIn data."""

from __future__ import annotations

import structlog

from app.models import DataQuality, ProfileData, ProviderCapabilities
from app.providers.linkedin.resolver import ResolvedProfileRecords

logger = structlog.get_logger(__name__)

SUPPORTED_SECTIONS = [
    "full_name",
    "headline",
    "location",
    "about",
    "experience",
    "education",
    "skills",
    "certifications",
    "languages",
    "profile_image_url",
]


class LinkedInNormalizer:
    """Transforms resolved records into normalized ProfileData and computes DataQuality."""

    @classmethod
    def get_capabilities(cls) -> ProviderCapabilities:
        """Return declared capabilities for the direct LinkedIn provider."""
        return ProviderCapabilities(
            provider_name="linkedin_direct",
            supported_sections=set(SUPPORTED_SECTIONS),
            unsupported_sections=set(),
            supports_realtime_polling=False,
            max_recommended_concurrency=2,
        )

    @classmethod
    def normalize(
        cls,
        resolved: ResolvedProfileRecords,
        canonical_url: str,
        raw_url: str | None = None,
        parser_failed_sections: list[str] | None = None,
    ) -> tuple[ProfileData, DataQuality]:
        """Normalize resolved records into domain model and calculate data quality.

        Args:
            resolved: Output from LinkedInResolver.
            canonical_url: Normalized LinkedIn canonical URL.
            raw_url: Original input URL supplied by caller.
            parser_failed_sections: Sections flagged as having schema/parsing failures.

        Returns:
            Tuple of (ProfileData, DataQuality).
        """
        failed_sections = parser_failed_sections or []

        profile = ProfileData(
            full_name=resolved.full_name,
            headline=resolved.headline,
            location=resolved.location,
            country_code=resolved.country_code,
            about=resolved.about,
            profile_image_url=resolved.profile_image_url,
            profile_url=raw_url or canonical_url,
            canonical_url=canonical_url,
            urn=resolved.urn,
            current_position=resolved.current_position,
            current_company=resolved.current_company,
            followers_count=resolved.followers_count,
            experience=resolved.experience,
            education=resolved.education,
            skills=resolved.skills,
            certifications=resolved.certifications,
            languages=resolved.languages,
        )

        data_quality = cls.calculate_data_quality(profile, failed_sections)
        return profile, data_quality

    @classmethod
    def calculate_data_quality(
        cls, profile: ProfileData, parser_failed_sections: list[str]
    ) -> DataQuality:
        """Calculate deterministic completeness score and categorize sections."""
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

        missing = [
            s
            for s in SUPPORTED_SECTIONS
            if s not in available and s not in parser_failed_sections
        ]

        total_supported = len(SUPPORTED_SECTIONS)
        completeness = (
            round(len(available) / total_supported, 2) if total_supported > 0 else 0.0
        )

        return DataQuality(
            available_sections=available,
            missing_sections=missing,
            unavailable_sections=[],
            parser_failed_sections=parser_failed_sections,
            completeness_score=completeness,
        )
