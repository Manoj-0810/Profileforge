"""Contract tests verifying raw Voyager fixtures parse deterministically to ProfileData."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models import ProfileData
from app.providers.linkedin.normalizer import LinkedInNormalizer
from app.providers.linkedin.parser import LinkedInParser
from app.providers.linkedin.resolver import LinkedInResolver

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"


@pytest.mark.parametrize(
    "fixture_name, expected_name, min_skills",
    [
        ("voyager_complete.json", "Sarah Jenkins", 4),
        ("voyager_partial.json", "Alex Mercer", 2),
        ("voyager_minimal.json", "Maya Lin", 2),
    ],
)
def test_voyager_fixtures_contract(
    fixture_name: str, expected_name: str, min_skills: int
):
    """Verify raw fixture normalization produces valid ProfileData domain instances."""
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"Missing fixture {fixture_name}"

    with open(fixture_path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    parsed = LinkedInParser.parse(raw_payload)
    resolved = LinkedInResolver.resolve(parsed)
    profile, dq = LinkedInNormalizer.normalize(
        resolved, canonical_url="https://www.linkedin.com/in/test-profile"
    )

    assert isinstance(profile, ProfileData)
    assert profile.full_name == expected_name
    assert len(profile.skills) >= min_skills
    assert dq.completeness_score > 0.0


def test_voyager_schema_drift_contract():
    """Verify malformed/drifted fixture triggers schema drift warning gracefully."""
    fixture_path = FIXTURES_DIR / "voyager_drift.json"
    with open(fixture_path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    parsed = LinkedInParser.parse(raw_payload)
    assert parsed.schema_drift_detected is True

    resolved = LinkedInResolver.resolve(parsed)
    _profile, dq = LinkedInNormalizer.normalize(
        resolved,
        canonical_url="https://www.linkedin.com/in/test-drift",
        parser_failed_sections=parsed.parser_failed_sections,
    )
    assert "profile_root" in dq.parser_failed_sections
