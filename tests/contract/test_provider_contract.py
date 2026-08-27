"""Provider contract test suite verifying raw upstream fixture transformation into ProfileData."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models import ProfileData
from app.providers.linkedapi.normalizer import LinkedAPINormalizer
from app.providers.linkedapi.parser import LinkedAPIParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"

FIXTURE_FILES = [
    "complete_profile.json",
    "partial_profile.json",
    "missing_about.json",
    "missing_image.json",
    "no_experience.json",
    "no_education.json",
    "multiple_experience.json",
    "multiple_education.json",
    "skills_only.json",
    "languages_response.json",
    "unexpected_fields.json",
    "minimal_profile.json",
    "localized_profile.json",
]


@pytest.mark.parametrize("filename", FIXTURE_FILES)
def test_provider_contract_fixture_transformation(filename: str):
    fixture_path = FIXTURES_DIR / filename
    assert fixture_path.exists(), f"Fixture file {filename} missing"

    with open(fixture_path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    parser = LinkedAPIParser()
    normalizer = LinkedAPINormalizer()

    canonical_url = "https://www.linkedin.com/in/test-contract-user"

    parsed = parser.parse(raw_payload)
    assert parsed.name, "Parsed profile must have non-empty name"

    profile = normalizer.normalize(parsed, canonical_url)
    assert isinstance(profile, ProfileData)
    assert profile.full_name == parsed.name
    assert profile.canonical_url == canonical_url

    # Invariants
    assert isinstance(profile.experience, list)
    assert isinstance(profile.education, list)
    assert isinstance(profile.skills, list)
    assert isinstance(profile.languages, list)
    assert isinstance(profile.certifications, list)
