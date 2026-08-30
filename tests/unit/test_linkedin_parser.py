"""Unit tests for LinkedIn Voyager normalized JSON parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.errors import ProfileForgeError
from app.providers.linkedin.parser import LinkedInParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"


def test_parser_extracts_all_entity_types():
    """Verify parser categorizes profile, positions, educations, skills, certifications, and languages."""
    fixture_path = FIXTURES_DIR / "voyager_complete.json"
    with open(fixture_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    parsed = LinkedInParser.parse(raw_data)

    assert not parsed.schema_drift_detected
    assert parsed.profile_entity["firstName"] == "Sarah"
    assert parsed.profile_entity["lastName"] == "Jenkins"
    assert len(parsed.positions) == 2
    assert len(parsed.educations) == 2
    assert len(parsed.skills) == 4
    assert len(parsed.certifications) == 1
    assert len(parsed.languages) == 2


def test_parser_partial_profile():
    """Verify parser extracts partial profiles without crashing."""
    fixture_path = FIXTURES_DIR / "voyager_partial.json"
    with open(fixture_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    parsed = LinkedInParser.parse(raw_data)

    assert not parsed.schema_drift_detected
    assert parsed.profile_entity["firstName"] == "Alex"
    assert len(parsed.positions) == 1
    assert len(parsed.educations) == 1
    assert len(parsed.skills) == 2
    assert len(parsed.certifications) == 0


def test_parser_detects_schema_drift_on_missing_profile():
    """Verify parser flags schema_drift_detected if root profile entity is absent."""
    fixture_path = FIXTURES_DIR / "voyager_drift.json"
    with open(fixture_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    parsed = LinkedInParser.parse(raw_data)
    assert parsed.schema_drift_detected is True
    assert "profile_root" in parsed.parser_failed_sections


def test_parser_rejects_non_dict_payload():
    """Verify parser raises UPSTREAM_SCHEMA_CHANGED if root is not a dictionary."""
    with pytest.raises(ProfileForgeError):
        LinkedInParser.parse(["not", "a", "dict"])  # type: ignore
