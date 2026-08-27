"""Unit tests for error taxonomy and HTTP status mapping."""

from __future__ import annotations

from app.errors import ERROR_STATUS_MAP, ErrorCode, ProfileForgeError


def test_all_error_codes_have_status_mapping():
    for code in ErrorCode:
        assert code in ERROR_STATUS_MAP
        assert 400 <= ERROR_STATUS_MAP[code] < 600


def test_profile_forge_error_attributes():
    err = ProfileForgeError(
        ErrorCode.INVALID_PROFILE_URL,
        "Bad URL",
        headers={"X-Test": "1"},
        details={"field": "url"},
    )
    assert err.error_code == ErrorCode.INVALID_PROFILE_URL
    assert err.status_code == 400
    assert err.headers == {"X-Test": "1"}
    assert err.details == {"field": "url"}
