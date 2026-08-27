"""Application configuration management using Pydantic Settings."""

from __future__ import annotations

from typing import Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Authentication
    API_KEYS: list[str] = Field(
        default_factory=lambda: ["test-api-key-123", "forge-secret-dev"],
        description="Comma-separated or list of authorized client API keys for X-API-Key header",
    )

    # LinkedAPI Credentials
    LINKEDAPI_TOKEN: str = Field(default="", description="LinkedAPI developer token")
    LINKEDAPI_IDENTIFICATION_TOKEN: str = Field(
        default="", description="LinkedAPI LinkedIn session identification token"
    )

    # Provider & Concurrency Configuration
    EXTRACTOR_TYPE: str = Field(
        default="mock",
        description="Active extractor provider: 'mock' (default for dev/test) or 'linkedapi'",
    )
    MAX_CONCURRENT_EXTRACTIONS: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Application semaphore bounding simultaneous in-flight extraction requests",
    )

    # Cache & Upstream Timeouts
    CACHE_TTL_SECONDS: int = Field(
        default=3600, ge=0, description="Cache retention duration in seconds"
    )
    UPSTREAM_TIMEOUT_SECONDS: float = Field(
        default=120.0,
        ge=5.0,
        description="Maximum deadline for upstream profile lookup",
    )
    LINKEDAPI_POLL_INTERVAL_SECONDS: float = Field(
        default=3.0, ge=0.5, description="Polling frequency for workflow status checks"
    )

    # Rate Limiting (per API key)
    RATE_LIMIT_REQUESTS: int = Field(
        default=60,
        ge=1,
        description="Maximum allowed requests within rate limit window",
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60, ge=1, description="Sliding window duration in seconds"
    )

    # Security & CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=list,
        description="List of allowed CORS origins (empty by default for security)",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment tier: development, staging, production",
    )


# Singleton instance
settings = Settings()


def save_env_credentials(
    linkedapi_token: str | None = None,
    identification_token: str | None = None,
    api_key: str | None = None,
    extractor_type: str | None = None,
) -> dict[str, Any]:
    """Persist credentials and configuration to .env file and update settings singleton."""
    from pathlib import Path

    env_path = Path(".env")
    current_vars: dict[str, str] = {}

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k, v = line_str.split("=", 1)
                current_vars[k.strip()] = v.strip()

    if linkedapi_token is not None:
        current_vars["LINKEDAPI_TOKEN"] = linkedapi_token
        settings.LINKEDAPI_TOKEN = linkedapi_token

    if identification_token is not None:
        current_vars["LINKEDAPI_IDENTIFICATION_TOKEN"] = identification_token
        settings.LINKEDAPI_IDENTIFICATION_TOKEN = identification_token

    if extractor_type is not None:
        current_vars["EXTRACTOR_TYPE"] = extractor_type
        settings.EXTRACTOR_TYPE = extractor_type

    if api_key is not None and api_key.strip():
        if api_key not in settings.API_KEYS:
            settings.API_KEYS.append(api_key)
        current_vars["API_KEYS"] = ",".join(settings.API_KEYS)

    out_lines = [f"{k}={v}" for k, v in current_vars.items()]
    env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    return {
        "status": "success",
        "extractor_type": settings.EXTRACTOR_TYPE,
        "has_linkedapi_token": bool(settings.LINKEDAPI_TOKEN),
        "has_identification_token": bool(settings.LINKEDAPI_IDENTIFICATION_TOKEN),
        "api_keys": settings.API_KEYS,
    }

