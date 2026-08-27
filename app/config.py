"""Application configuration management using Pydantic Settings."""

from __future__ import annotations

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
