"""Normalizes resolved provider entities into domain models with provider-aware DataQuality scoring."""

from __future__ import annotations

from app.models import DataQuality, ProfileData, ProviderCapabilities
from app.providers.linkedapi.parser import ParsedRawProfile
from app.providers.linkedapi.resolver import LinkedAPIResolver

LINKEDAPI_CAPABILITIES = ProviderCapabilities(
    provider_name="linkedapi",
    supported_sections={
        "full_name",
        "headline",
        "location",
        "experience",
        "education",
        "skills",
        "languages",
    },
    unsupported_sections={
        "certifications",
        "about",
        "profile_image_url",
    },
    supports_realtime_polling=True,
    max_recommended_concurrency=2,
)


class LinkedAPINormalizer:
    """Normalizes parsed and resolved records into clean ProfileData."""

    def __init__(
        self,
        capabilities: ProviderCapabilities | None = None,
        resolver: LinkedAPIResolver | None = None,
    ) -> None:
        self.capabilities = capabilities or LINKEDAPI_CAPABILITIES
        self.resolver = resolver or LinkedAPIResolver()

    def compute_data_quality(
        self,
        parsed: ParsedRawProfile,
        experiences_count: int,
        educations_count: int,
        languages_count: int,
    ) -> DataQuality:
        """Compute provider-aware DataQuality and deterministic completeness score."""
        available: list[str] = []
        missing: list[str] = []
        unavailable: list[str] = []

        # Check supported sections
        if parsed.name:
            available.append("full_name")
        else:
            missing.append("full_name")

        if parsed.headline:
            available.append("headline")
        else:
            missing.append("headline")

        if parsed.location:
            available.append("location")
        else:
            missing.append("location")

        if experiences_count > 0:
            available.append("experience")
        else:
            missing.append("experience")

        if educations_count > 0:
            available.append("education")
        else:
            missing.append("education")

        if len(parsed.skills_list) > 0:
            available.append("skills")
        else:
            missing.append("skills")

        if languages_count > 0:
            available.append("languages")
        else:
            missing.append("languages")

        # Handle provisional / unexposed sections
        if parsed.about:
            available.append("about")
        else:
            unavailable.append("about")

        if parsed.profile_image_url:
            available.append("profile_image_url")
        else:
            unavailable.append("profile_image_url")

        # Certifications are not exposed by primary LinkedAPI action set
        unavailable.append("certifications")

        # Completeness ratio calculated strictly against supported sections
        supported_total = len(self.capabilities.supported_sections)
        # Filter available by supported sections
        supported_available = [
            s for s in available if s in self.capabilities.supported_sections
        ]

        score = (
            round(len(supported_available) / supported_total, 2)
            if supported_total > 0
            else 0.0
        )

        return DataQuality(
            available_sections=available,
            missing_sections=missing,
            unavailable_sections=unavailable,
            parser_failed_sections=parsed.parser_failed_sections,
            completeness_score=score,
        )

    def normalize(
        self,
        parsed: ParsedRawProfile,
        canonical_url: str,
    ) -> ProfileData:
        """Transform parsed profile into normalized domain model."""
        experiences, educations, languages = self.resolver.resolve(parsed)

        # Fallback current position / company from experience if not present at top level
        current_pos = parsed.current_position
        current_comp = parsed.current_company_name
        if not current_pos and experiences:
            current_pos = experiences[0].title
        if not current_comp and experiences:
            current_comp = experiences[0].company

        return ProfileData(
            full_name=parsed.name,
            headline=parsed.headline,
            location=parsed.location,
            country_code=parsed.country_code,
            about=parsed.about,
            profile_image_url=parsed.profile_image_url,
            profile_url=parsed.public_url or canonical_url,
            canonical_url=canonical_url,
            urn=parsed.urn,
            current_position=current_pos,
            current_company=current_comp,
            followers_count=parsed.followers_count,
            experience=experiences,
            education=educations,
            skills=parsed.skills_list,
            certifications=[],
            languages=languages,
        )
