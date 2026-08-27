"""Provider contract tests asserting structural drift detection and error classification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.providers.linkedapi.client import LinkedAPIClient
from app.providers.linkedapi.parser import LinkedAPIParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"


def test_schema_drift_fixture_raises_upstream_schema_changed():
    drift_path = FIXTURES_DIR / "schema_drift.json"
    with open(drift_path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    parser = LinkedAPIParser()
    with pytest.raises(ProfileForgeError) as exc_info:
        parser.parse(raw_payload)

    assert exc_info.value.error_code == ErrorCode.UPSTREAM_SCHEMA_CHANGED
    assert exc_info.value.status_code == 502


def test_error_not_found_fixture_classification():
    path = FIXTURES_DIR / "error_not_found.json"
    with open(path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    client = LinkedAPIClient(api_token="test", identification_token="test")
    # Extract error dict from fixture
    error_dict = raw_payload["data"]["then"][0]["error"]
    err = client._classify_error_response(error_dict)
    assert err.error_code == ErrorCode.PROFILE_NOT_FOUND
    assert err.status_code == 404


def test_error_auth_fixture_classification():
    path = FIXTURES_DIR / "error_auth.json"
    with open(path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    client = LinkedAPIClient(api_token="test", identification_token="test")
    err = client._classify_error_response(raw_payload["error"])
    assert err.error_code == ErrorCode.AUTH_CONFIGURATION_ERROR
    assert err.status_code == 503


def test_error_rate_limited_fixture_classification():
    path = FIXTURES_DIR / "error_rate_limited.json"
    with open(path, encoding="utf-8") as f:
        raw_payload = json.load(f)

    client = LinkedAPIClient(api_token="test", identification_token="test")
    err = client._classify_error_response(raw_payload["error"])
    assert err.error_code == ErrorCode.UPSTREAM_RATE_LIMITED
    assert err.status_code == 502
