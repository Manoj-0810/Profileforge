"""Tests for deployment configuration guardrails."""

from __future__ import annotations

import pytest

from app.config import Settings


def make_settings(**overrides: object) -> Settings:
    """Create isolated settings without reading the developer's .env file."""
    return Settings(_env_file=None, **overrides)


def test_production_rejects_default_client_keys() -> None:
    config = make_settings(ENVIRONMENT="production", API_KEYS=["test-api-key-123"])

    with pytest.raises(ValueError, match="Production requires API_KEYS"):
        config.validate_runtime_configuration()


def test_production_rejects_template_client_keys() -> None:
    config = make_settings(
        ENVIRONMENT="production", API_KEYS=["your-client-api-key-here"]
    )

    with pytest.raises(ValueError, match="Production requires API_KEYS"):
        config.validate_runtime_configuration()


def test_production_linkedin_requires_both_session_cookies() -> None:
    config = make_settings(
        ENVIRONMENT="production",
        API_KEYS=["a-real-client-key"],
        EXTRACTOR_TYPE="linkedin",
        LINKEDIN_LI_AT="li-at-present",
        LINKEDIN_JSESSIONID="",
    )

    with pytest.raises(ValueError, match="LINKEDIN_LI_AT"):
        config.validate_runtime_configuration()


def test_mock_development_configuration_is_valid() -> None:
    config = make_settings(ENVIRONMENT="development", EXTRACTOR_TYPE="mock")
    config.validate_runtime_configuration()


def test_api_keys_are_trimmed_and_empty_values_removed() -> None:
    config = make_settings(API_KEYS=" first-key, , second-key ")
    assert config.API_KEYS == ["first-key", "second-key"]
