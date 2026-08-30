"""Unit tests for direct LinkedIn domain normalizer and data quality calculator."""

from __future__ import annotations

from app.models import ExperienceEntry, LanguageEntry
from app.providers.linkedin.normalizer import LinkedInNormalizer
from app.providers.linkedin.resolver import ResolvedProfileRecords


def test_normalizer_complete_profile_data_quality():
    """Verify complete profile scores 1.0 with all 10 sections present."""
    resolved = ResolvedProfileRecords(
        full_name="Sarah Jenkins",
        headline="Staff Software Engineer",
        location="San Francisco, CA",
        country_code="US",
        about="Experienced engineer",
        profile_image_url="https://media.licdn.com/dms/image/avatar.jpg",
        urn="urn:li:fsd_profile:123",
        experience=[ExperienceEntry(title="Engineer", company="TechCorp")],
        education=[],
        skills=["Python"],
        certifications=[],
        languages=[LanguageEntry(name="English")],
    )

    profile, dq = LinkedInNormalizer.normalize(
        resolved, canonical_url="https://www.linkedin.com/in/sarah-jenkins"
    )

    assert profile.full_name == "Sarah Jenkins"
    assert profile.canonical_url == "https://www.linkedin.com/in/sarah-jenkins"
    assert "full_name" in dq.available_sections
    assert "headline" in dq.available_sections
    assert "location" in dq.available_sections
    assert "about" in dq.available_sections
    assert "experience" in dq.available_sections
    assert "skills" in dq.available_sections
    assert "languages" in dq.available_sections
    assert "profile_image_url" in dq.available_sections
    assert "education" in dq.missing_sections
    assert "certifications" in dq.missing_sections
    assert dq.completeness_score == 0.80


def test_normalizer_handles_parser_failed_sections():
    """Verify parser failures are reflected in parser_failed_sections without inflating missing sections."""
    resolved = ResolvedProfileRecords(full_name="N/A")
    _, dq = LinkedInNormalizer.normalize(
        resolved,
        canonical_url="https://www.linkedin.com/in/test",
        parser_failed_sections=["full_name", "headline"],
    )

    assert "full_name" in dq.parser_failed_sections
    assert "headline" in dq.parser_failed_sections
    assert "full_name" not in dq.missing_sections
    assert "headline" not in dq.missing_sections
