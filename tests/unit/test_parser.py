"""Unit tests for LinkedAPI structural parser and drift detection."""

from __future__ import annotations

import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.providers.linkedapi.parser import LinkedAPIParser


def test_parse_valid_completion_payload():
    parser = LinkedAPIParser()
    payload = {
        "actionType": "st.openPersonPage",
        "success": True,
        "data": {
            "name": "Jane Doe",
            "headline": "Lead Architect",
            "location": "Seattle, WA",
            "then": [
                {
                    "actionType": "st.retrievePersonSkills",
                    "data": [{"name": "Rust"}, {"name": "Python"}],
                }
            ],
        },
    }

    parsed = parser.parse(payload)
    assert parsed.name == "Jane Doe"
    assert parsed.headline == "Lead Architect"
    assert parsed.skills_list == ["Rust", "Python"]
    assert parsed.parser_failed_sections == []


def test_parse_missing_data_dict_raises_502():
    parser = LinkedAPIParser()
    with pytest.raises(ProfileForgeError) as exc_info:
        parser.parse({"actionType": "st.openPersonPage", "success": True})
    assert exc_info.value.error_code == ErrorCode.UPSTREAM_SCHEMA_CHANGED
    assert exc_info.value.status_code == 502


def test_parse_missing_name_raises_502():
    parser = LinkedAPIParser()
    with pytest.raises(ProfileForgeError) as exc_info:
        parser.parse({"data": {"headline": "No name person"}})
    assert exc_info.value.error_code == ErrorCode.UPSTREAM_SCHEMA_CHANGED
    assert exc_info.value.status_code == 502


def test_parse_malformed_section_recorded_in_failed_sections():
    parser = LinkedAPIParser()
    payload = {
        "data": {
            "name": "Alex Drift",
            "then": [
                {
                    "actionType": "st.retrievePersonExperience",
                    "data": "this-should-be-a-list-not-a-string",
                }
            ],
        }
    }
    parsed = parser.parse(payload)
    assert parsed.name == "Alex Drift"
    assert "experience" in parsed.parser_failed_sections
