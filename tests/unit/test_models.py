"""Unit tests for domain models and data quality metrics."""

from __future__ import annotations

import json

from app.models import (
    DataQuality,
    EducationEntry,
    ExperienceEntry,
    ProfileData,
    ProfileLookupRequest,
    ProviderCapabilities,
)


def test_provider_capabilities_defaults():
    caps = ProviderCapabilities(provider_name="test_provider")
    assert caps.provider_name == "test_provider"
    assert "full_name" in caps.supported_sections
    assert "headline" in caps.supported_sections
    assert "certifications" in caps.supported_sections
    assert len(caps.unsupported_sections) == 0
    assert caps.supports_realtime_polling is False


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
    assert edu.field_of_study == "Computer Science"


def test_data_quality_score_bounds():
    dq = DataQuality(
        available_sections=["name", "headline"],
        missing_sections=["about"],
        completeness_score=0.67,
    )
    assert dq.completeness_score == 0.67
    assert len(dq.available_sections) == 2


def test_profile_data_minimal():
    profile = ProfileData(
        full_name="Jane Doe",
        profile_url="https://www.linkedin.com/in/janedoe",
        canonical_url="https://www.linkedin.com/in/janedoe",
    )
    assert profile.full_name == "Jane Doe"
    assert profile.experience == []
    assert profile.education == []
    assert profile.skills == []


def test_profile_lookup_request_schema_example_validity():
    """Assert ProfileLookupRequest schema example is valid JSON and parses correctly."""
    schema = ProfileLookupRequest.model_json_schema()
    assert "example" in schema or "examples" in schema
    example = schema.get("example") or schema.get("examples", [{}])[0]

    # Must serialize and deserialize cleanly
    json_str = json.dumps(example)
    parsed = json.loads(json_str)

    # Must validate cleanly as ProfileLookupRequest
    req = ProfileLookupRequest.model_validate(parsed)
    assert req.url == "https://www.linkedin.com/in/sarah-jenkins-dev"
    assert req.bypass_cache is False
