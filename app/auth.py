"""API Key authentication dependency for ProfileForge."""

from __future__ import annotations

import secrets

import structlog
from fastapi import Header

from app.config import settings
from app.errors import ErrorCode, ProfileForgeError

logger = structlog.get_logger(__name__)


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Validate X-API-Key header using constant-time comparison against configured authorized keys.

    Args:
        x_api_key: Value from incoming HTTP header.

    Returns:
        Validated API key string.

    Raises:
        ProfileForgeError: 401 Unauthorized if key is missing or invalid.
    """
    if not x_api_key:
        logger.warning("auth_failed_missing_api_key")
        raise ProfileForgeError(
            ErrorCode.UNAUTHORIZED,
            "Authentication required. Please provide a valid API key in the 'X-API-Key' header.",
            status_code=401,
        )

    valid_keys = settings.API_KEYS
    is_valid = any(secrets.compare_digest(x_api_key, key) for key in valid_keys)

    if not is_valid:
        masked_key = f"{x_api_key[:4]}..." if len(x_api_key) >= 4 else "..."
        logger.warning("auth_failed_invalid_api_key", key_prefix=masked_key)
        raise ProfileForgeError(
            ErrorCode.UNAUTHORIZED,
            "Invalid API key provided in 'X-API-Key' header.",
            status_code=401,
        )

    return x_api_key
