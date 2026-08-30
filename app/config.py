"""Application configuration management using Pydantic Settings."""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_API_KEYS = ["test-api-key-123", "forge-secret-dev"]
INSECURE_API_KEY_VALUES = {
    *DEFAULT_DEV_API_KEYS,
    "your-client-api-key-here",
    "another-api-key",
    "change-me",
    "changeme",
}
SUPPORTED_EXTRACTORS = {"mock", "linkedin"}


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Authentication
    API_KEYS: list[str] | str = Field(
        default_factory=lambda: list(DEFAULT_DEV_API_KEYS),
        description="Comma-separated or list of authorized client API keys for X-API-Key header",
    )

    @field_validator("API_KEYS", mode="after")
    @classmethod
    def parse_api_keys(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    res = json.loads(v)
                    if isinstance(res, list):
                        return [str(key).strip() for key in res if str(key).strip()]
                except (json.JSONDecodeError, ValueError):
                    pass
            return [k.strip() for k in v.split(",") if k.strip()]
        if isinstance(v, list):
            return [str(key).strip() for key in v if str(key).strip()]
        return list(DEFAULT_DEV_API_KEYS)

    # Direct LinkedIn Credentials & Session Settings
    LINKEDIN_LI_AT: str = Field(
        default="",
        description="LinkedIn li_at session cookie from authorized session",
    )
    LINKEDIN_JSESSIONID: str = Field(
        default="",
        description="LinkedIn JSESSIONID session cookie used for CSRF token derivation",
    )
    LINKEDIN_USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        description="Realistic User-Agent for direct HTTP requests",
    )
    LINKEDIN_PROXY_URL: str | None = Field(
        default=None,
        description="Optional proxy URL for routing direct LinkedIn requests",
    )

    # Provider & Concurrency Configuration
    EXTRACTOR_TYPE: str = Field(
        default="mock",
        description="Active extractor provider: 'mock' (default for dev/test) or 'linkedin'",
    )

    @field_validator("EXTRACTOR_TYPE", "ENVIRONMENT", mode="before")
    @classmethod
    def normalize_modes(cls, v: Any) -> str:
        """Normalize deployment mode values before they control application wiring."""
        return str(v).strip().lower()

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
        default=30.0,
        ge=5.0,
        description="Maximum deadline for upstream profile lookup in seconds",
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
    CORS_ORIGINS: list[str] | str = Field(
        default_factory=list,
        description="List of allowed CORS origins (empty by default for security)",
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    res = json.loads(v)
                    if isinstance(res, list):
                        return res
                except (json.JSONDecodeError, ValueError):
                    pass
            return [k.strip() for k in v.split(",") if k.strip()]
        if isinstance(v, list):
            return v
        return []

    ENVIRONMENT: str = Field(
        default="development",
        description="Environment tier: development, staging, production",
    )

    def validate_runtime_configuration(self) -> None:
        """Fail fast on configurations that would make a deployment misleading or unsafe."""
        environment = self.ENVIRONMENT.strip().lower()
        extractor = self.EXTRACTOR_TYPE.strip().lower()

        if extractor not in SUPPORTED_EXTRACTORS:
            raise ValueError(
                f"EXTRACTOR_TYPE must be one of {sorted(SUPPORTED_EXTRACTORS)}"
            )

        if environment == "production":
            if not self.API_KEYS or any(
                key.lower() in INSECURE_API_KEY_VALUES or not key.strip()
                for key in self.API_KEYS
            ):
                raise ValueError(
                    "Production requires API_KEYS containing non-default client keys."
                )
            if extractor == "linkedin" and not (
                self.LINKEDIN_LI_AT.strip() and self.LINKEDIN_JSESSIONID.strip()
            ):
                raise ValueError(
                    "Production LinkedIn mode requires LINKEDIN_LI_AT and "
                    "LINKEDIN_JSESSIONID."
                )


# Singleton instance
settings = Settings()
