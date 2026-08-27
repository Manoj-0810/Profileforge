"""Unit tests for domain models and data quality metrics."""

from __future__ import annotations

from app.models import (
    DataQuality,
    EducationEntry,
    ExperienceEntry,
    ProfileData,
    ProviderCapabilities,
)


def test_provider_capabilities_defaults():
    caps = ProviderCapabilities(provider_name="test_provider")
    assert caps.provider_name == "test_provider"
    assert "full_name" in caps.supported_sections
    assert "certifications" in caps.unsupported_sections
    assert caps.supports_realtime_polling is True


def test_experience_entry_creation():
    exp = ExperienceEntry(
        title="Principal Engineer",
        company="Tech Corp",
        duration_months=24,
        start_date="2024-01-01T00:00:00Z",
    )
    assert exp.title == "Principal Engineer"
    assert exp.company == "Tech Corp"
    assert exp.duration_months == 24
    assert exp.end_date is None


def test_education_entry_creation():
    edu = EducationEntry(
        school="Stanford University",
        degree="Master of Science",
        field_of_study="Computer Science",
    )
    assert edu.school == "Stanford University"
    assert edu.degree == "Master of Science"


def test_data_quality_score_bounds():
    dq = DataQuality(
        available_sections=["full_name", "headline", "location"],
        missing_sections=["experience"],
        unavailable_sections=["certifications"],
        completeness_score=0.75,
    )
    assert dq.completeness_score == 0.75
    assert len(dq.available_sections) == 3


def test_profile_data_minimal():
    profile = ProfileData(
        full_name="Alice Smith",
        profile_url="https://www.linkedin.com/in/alice-smith",
        canonical_url="https://www.linkedin.com/in/alice-smith",
    )
    assert profile.full_name == "Alice Smith"
    assert profile.experience == []
    assert profile.skills == []
