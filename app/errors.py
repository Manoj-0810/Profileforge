"""Standardized error codes and exceptions for ProfileForge."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Machine-readable application error taxonomy."""

    INVALID_PROFILE_URL = "INVALID_PROFILE_URL"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTH_CONFIGURATION_ERROR = "AUTH_CONFIGURATION_ERROR"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_INACCESSIBLE = "PROFILE_INACCESSIBLE"
    UPSTREAM_AUTH_FAILED = "UPSTREAM_AUTH_FAILED"
    UPSTREAM_RATE_LIMITED = "UPSTREAM_RATE_LIMITED"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_CHALLENGE_DETECTED = "UPSTREAM_CHALLENGE_DETECTED"
    UPSTREAM_SERVER_ERROR = "UPSTREAM_SERVER_ERROR"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_SCHEMA_CHANGED = "UPSTREAM_SCHEMA_CHANGED"
    PARSER_FAILURE = "PARSER_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Default HTTP status code mappings for each domain ErrorCode
ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.INVALID_PROFILE_URL: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.PROFILE_NOT_FOUND: 404,
    ErrorCode.AUTH_CONFIGURATION_ERROR: 503,
    ErrorCode.PROFILE_INACCESSIBLE: 502,
    ErrorCode.UPSTREAM_AUTH_FAILED: 502,
    ErrorCode.UPSTREAM_RATE_LIMITED: 502,
    ErrorCode.UPSTREAM_TIMEOUT: 504,
    ErrorCode.UPSTREAM_CHALLENGE_DETECTED: 502,
    ErrorCode.UPSTREAM_SERVER_ERROR: 502,
    ErrorCode.UPSTREAM_UNAVAILABLE: 502,
    ErrorCode.UPSTREAM_SCHEMA_CHANGED: 502,
    ErrorCode.PARSER_FAILURE: 502,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ProfileForgeError(Exception):
    """Base application exception with correlated error code and HTTP status."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code or ERROR_STATUS_MAP.get(error_code, 500)
        self.headers = headers or {}
        self.details = details or {}
