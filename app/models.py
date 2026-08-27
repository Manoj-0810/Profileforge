"""Domain models and schema definitions for ProfileForge.

This module defines provider-independent Pydantic v2 schemas used across the API,
service layer, and data normalizers.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class ProviderCapabilities(BaseModel):
    """Declares the extraction capabilities of a specific upstream provider."""

    model_config = ConfigDict(frozen=True)

    provider_name: str
    supported_sections: set[str] = Field(
        default_factory=lambda: {
            "full_name",
            "headline",
            "location",
            "experience",
            "education",
            "skills",
            "languages",
        }
    )
    unsupported_sections: set[str] = Field(
        default_factory=lambda: {
            "certifications",
            "about",
            "profile_image_url",
        }
    )
    supports_realtime_polling: bool = True
    max_recommended_concurrency: int = 2


class ExperienceEntry(BaseModel):
    """Represents a single employment or professional experience entry."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(description="Job title or position held")
    company: str = Field(description="Name of the employing organization")
    company_url: str | None = Field(
        default=None, description="LinkedIn URL or identifier for company"
    )
    employment_type: str | None = Field(
        default=None, description="e.g. fullTime, partTime, contract"
    )
    location_type: str | None = Field(
        default=None, description="e.g. onSite, remote, hybrid"
    )
    description: str | None = Field(
        default=None, description="Detailed role description or achievements"
    )
    duration_months: int | None = Field(
        default=None, description="Duration in months if available"
    )
    start_date: str | None = Field(
        default=None, description="ISO 8601 start date or year string"
    )
    end_date: str | None = Field(
        default=None, description="ISO 8601 end date, year string, or null for current"
    )
    location: str | None = Field(
        default=None, description="Geographic location of role"
    )


class EducationEntry(BaseModel):
    """Represents an academic degree, diploma, or educational program."""

    model_config = ConfigDict(extra="ignore")

    school: str = Field(description="Name of the university or institution")
    school_url: str | None = Field(
        default=None, description="LinkedIn URL or identifier for institution"
    )
    details: str | None = Field(
        default=None, description="Raw details string if present"
    )
    degree: str | None = Field(
        default=None, description="e.g. Bachelor of Science, Master of Arts"
    )
    field_of_study: str | None = Field(
        default=None, description="Major or specialization field"
    )
    start_date: str | None = Field(
        default=None, description="Start date or year string"
    )
    end_date: str | None = Field(
        default=None, description="End date, graduation year, or null"
    )


class CertificationEntry(BaseModel):
    """Represents a professional license or certification."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Name of certification")
    issuing_organization: str = Field(
        description="Organization that issued certification"
    )
    issue_date: str | None = Field(default=None, description="Issue date string")
    expiration_date: str | None = Field(
        default=None, description="Expiration date string"
    )
    credential_id: str | None = Field(
        default=None, description="Credential ID or license number"
    )
    credential_url: str | None = Field(default=None, description="Verification URL")


class LanguageEntry(BaseModel):
    """Represents a language and associated proficiency level."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Language name (e.g. English, German)")
    proficiency: str | None = Field(
        default=None,
        description="e.g. Native or bilingual, Full professional, Elementary",
    )


class DataQuality(BaseModel):
    """Reflects extraction completeness and data quality metrics."""

    model_config = ConfigDict(extra="ignore")

    available_sections: list[str] = Field(
        default_factory=list,
        description="Sections successfully extracted with non-empty content",
    )
    missing_sections: list[str] = Field(
        default_factory=list,
        description="Supported sections that were empty or absent on the target profile",
    )
    unavailable_sections: list[str] = Field(
        default_factory=list,
        description="Sections unexposed or unsupported by active provider capabilities",
    )
    parser_failed_sections: list[str] = Field(
        default_factory=list,
        description="Sections where structural schema parsing failed",
    )
    completeness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Deterministic ratio |available| / |supported|",
    )


class ProfileData(BaseModel):
    """Normalized domain model representing all extracted profile information."""

    model_config = ConfigDict(extra="ignore")

    full_name: str = Field(description="Full legal or display name")
    headline: str | None = Field(
        default=None, description="Professional headline or role summary"
    )
    location: str | None = Field(default=None, description="Geographic location string")
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code"
    )
    about: str | None = Field(default=None, description="Summary or about section text")
    profile_image_url: str | None = Field(
        default=None, description="Public avatar or picture URL"
    )
    profile_url: str = Field(description="Input or canonical profile URL")
    canonical_url: str = Field(description="Strict normalized canonical LinkedIn URL")
    urn: str | None = Field(
        default=None, description="LinkedIn Member URN (e.g. urn:li:member:123)"
    )
    current_position: str | None = Field(
        default=None, description="Current primary job title"
    )
    current_company: str | None = Field(
        default=None, description="Current primary employer name"
    )
    followers_count: int | None = Field(
        default=None, description="Public follower count"
    )
    experience: list[ExperienceEntry] = Field(
        default_factory=list, description="Chronological work history"
    )
    education: list[EducationEntry] = Field(
        default_factory=list, description="Academic background"
    )
    skills: list[str] = Field(
        default_factory=list, description="List of recognized skills"
    )
    certifications: list[CertificationEntry] = Field(
        default_factory=list, description="Certifications and licenses"
    )
    languages: list[LanguageEntry] = Field(
        default_factory=list, description="Spoken and written languages"
    )


class ProfileLookupRequest(BaseModel):
    """Incoming request body for profile lookup."""

    url: str = Field(
        ...,
        description="Public LinkedIn profile URL (e.g. https://www.linkedin.com/in/username)",
        examples=["https://www.linkedin.com/in/sarah-jenkins-dev"],
    )


class ProfileLookupResponse(BaseModel):
    """Top-level structured JSON response for successful profile lookup."""

    profile: ProfileData = Field(
        description="Extracted and normalized profile information"
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when data was extracted",
    )
    cache_hit: bool = Field(
        default=False, description="True if served from cache, False if fresh fetch"
    )
    source: str = Field(
        default="linkedapi", description="Extraction provider identifier"
    )
    request_id: str = Field(description="Unique correlation ID for tracing")
    data_quality: DataQuality = Field(description="Completeness and quality assessment")


class ErrorDetails(BaseModel):
    """Standardized error envelope."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable explanation of failure")
    request_id: str | None = Field(
        default=None, description="Correlation ID for error investigation"
    )


class ErrorResponse(BaseModel):
    """Standard error response payload."""

    error: ErrorDetails
