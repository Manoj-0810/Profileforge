"""Unit tests for LinkedAPIResolver degree extraction and entity mapping."""

from __future__ import annotations

from app.providers.linkedapi.parser import RawEducation, RawExperience, RawLanguage
from app.providers.linkedapi.resolver import LinkedAPIResolver


def test_resolve_education_degree_and_major():
    resolver = LinkedAPIResolver()
    raw = RawEducation(
        schoolName="Harvard University",
        schoolHashedUrl="https://linkedin.com/company/harvard",
        details="Master of Science in Computer Science, Artificial Intelligence",
    )
    resolved = resolver.resolve_education_entry(raw)
    assert resolved.school == "Harvard University"
    assert resolved.degree == "Master of Science"
    assert resolved.field_of_study == "Computer Science, Artificial Intelligence"


def test_resolve_education_fallback():
    resolver = LinkedAPIResolver()
    raw = RawEducation(
        schoolName="Oxford University",
        details="Certificate of Advanced Studies",
    )
    resolved = resolver.resolve_education_entry(raw)
    assert resolved.school == "Oxford University"
    assert resolved.degree == "Certificate of Advanced Studies"


def test_resolve_experience_entry():
    resolver = LinkedAPIResolver()
    raw = RawExperience(
        position="Senior Staff Engineer",
        companyName="Stripe",
        companyHashedUrl="https://linkedin.com/company/stripe",
        duration=36,
        description="Scaling infrastructure.",
    )
    resolved = resolver.resolve_experience_entry(raw)
    assert resolved.title == "Senior Staff Engineer"
    assert resolved.company == "Stripe"
    assert resolved.duration_months == 36


def test_resolve_language_entry():
    resolver = LinkedAPIResolver()
    raw = RawLanguage(name="French", proficiency="Native or bilingual")
    resolved = resolver.resolve_language_entry(raw)
    assert resolved.name == "French"
    assert resolved.proficiency == "Native or bilingual"
