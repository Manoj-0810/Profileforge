"""Structured JSON logging configuration and request correlation middleware."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

SENSITIVE_HEADERS = {
    "authorization",
    "x-api-key",
    "linked-api-token",
    "identification-token",
    "cookie",
    "set-cookie",
}


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact sensitive header values for observability safety."""
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return sanitized


def setup_logging(environment: str = "development") -> None:
    """Configure structlog processors and standard library logging integration."""
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware attaching request_id and emitting structured access logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter()
        status_code = 500
        error_code = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            raise
        finally:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger = structlog.get_logger("access")
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms,
                error_code=error_code,
            )
