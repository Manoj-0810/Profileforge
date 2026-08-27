"""Unit tests for LinkedAPINormalizer and provider-aware DataQuality calculations."""

from __future__ import annotations

from app.providers.linkedapi.normalizer import LinkedAPINormalizer
from app.providers.linkedapi.parser import ParsedRawProfile, RawExperience


def test_normalizer_complete_profile():
    normalizer = LinkedAPINormalizer()
    parsed = ParsedRawProfile(
        name="Sarah Jenkins",
        headline="Staff Engineer",
        location="Seattle, WA",
        skills_list=["Python", "Go"],
    )
    dq = normalizer.compute_data_quality(
        parsed, experiences_count=2, educations_count=1, languages_count=1
    )

    # 7 supported sections in LinkedAPI: full_name, headline, location, experience, education, skills, languages
    # All 7 present -> completeness_score == 1.0
    assert dq.completeness_score == 1.0
    assert len(dq.missing_sections) == 0
    assert "certifications" in dq.unavailable_sections


def test_normalizer_partial_profile():
    normalizer = LinkedAPINormalizer()
    parsed = ParsedRawProfile(
        name="Alex Mercer",
        headline="Developer",
        location="Austin, TX",
        skills_list=[],
    )
    # missing experience, education, skills, languages (3 out of 7 present)
    dq = normalizer.compute_data_quality(
        parsed, experiences_count=0, educations_count=0, languages_count=0
    )
    assert dq.completeness_score == round(3 / 7, 2)
    assert "experience" in dq.missing_sections
    assert "education" in dq.missing_sections
    assert "skills" in dq.missing_sections
    assert "languages" in dq.missing_sections


def test_normalizer_fallback_current_role_from_experience():
    normalizer = LinkedAPINormalizer()
    parsed = ParsedRawProfile(
        name="Elena NoTopRole",
        current_position=None,
        current_company_name=None,
        experience_list=[
            RawExperience(
                position="Principal Scientist",
                companyName="AI Labs",
            )
        ],
    )
    profile = normalizer.normalize(parsed, "https://www.linkedin.com/in/elena")
    assert profile.current_position == "Principal Scientist"
    assert profile.current_company == "AI Labs"
