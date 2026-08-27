"""Main FastAPI application entry point for ProfileForge."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.cache import InMemoryCache
from app.config import settings
from app.errors import ErrorCode, ProfileForgeError
from app.extractor.base import ProfileExtractor
from app.extractor.linkedin import LinkedInExtractor
from app.extractor.mock import MockExtractor
from app.logging_config import RequestLoggingMiddleware, setup_logging
from app.models import (
    ErrorDetails,
    ErrorResponse,
    ProfileLookupRequest,
    ProfileLookupResponse,
)
from app.providers.linkedapi.client import LinkedAPIClient
from app.rate_limit import rate_limit_dependency
from app.services.profile_service import ProfileService

logger = structlog.get_logger(__name__)

# Global cache and service instances
cache_instance = InMemoryCache(default_ttl_seconds=settings.CACHE_TTL_SECONDS)


def create_profile_service() -> ProfileService:
    """Factory creating ProfileService configured for the active environment."""
    extractor: ProfileExtractor
    if settings.EXTRACTOR_TYPE == "linkedapi":
        client = LinkedAPIClient(
            api_token=settings.LINKEDAPI_TOKEN,
            identification_token=settings.LINKEDAPI_IDENTIFICATION_TOKEN,
            timeout_seconds=settings.UPSTREAM_TIMEOUT_SECONDS,
            poll_interval_seconds=settings.LINKEDAPI_POLL_INTERVAL_SECONDS,
        )
        extractor = LinkedInExtractor(client=client)
    else:
        extractor = MockExtractor()

    return ProfileService(
        extractor=extractor,
        cache=cache_instance,
        max_concurrency=settings.MAX_CONCURRENT_EXTRACTIONS,
    )


profile_service = create_profile_service()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifespan hook."""
    setup_logging(environment=settings.ENVIRONMENT)
    logger.info(
        "profileforge_startup",
        extractor=settings.EXTRACTOR_TYPE,
        environment=settings.ENVIRONMENT,
        max_concurrency=settings.MAX_CONCURRENT_EXTRACTIONS,
    )
    yield
    logger.info("profileforge_shutdown")


app = FastAPI(
    title="ProfileForge API",
    description="High-reliability Profile Lookup API returning normalized LinkedIn profile data.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.add_middleware(RequestLoggingMiddleware)


# Global Exception Handlers
@app.exception_handler(ProfileForgeError)
async def handle_profile_forge_error(
    request: Request, exc: ProfileForgeError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorResponse(
        error=ErrorDetails(
            code=exc.error_code.value,
            message=exc.message,
            request_id=request_id,
        )
    )
    headers = {"X-Request-ID": request_id} if request_id else {}
    headers.update(exc.headers)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorResponse(
        error=ErrorDetails(
            code=ErrorCode.INVALID_PROFILE_URL.value,
            message=f"Request validation failed: {exc.errors()[0].get('msg', 'Invalid body')}",
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_payload.model_dump(),
        headers={"X-Request-ID": request_id} if request_id else {},
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception("unhandled_internal_error", error=str(exc), request_id=request_id)
    error_payload = ErrorResponse(
        error=ErrorDetails(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="An internal server error occurred while processing the request.",
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
        headers={"X-Request-ID": request_id} if request_id else {},
    )


# Root Endpoint
@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    """Root landing endpoint providing API metadata and documentation links."""
    return {
        "service": "ProfileForge API",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/healthz",
        "readiness_check": "/readyz",
        "lookup_endpoint": "POST /v1/profile",
        "message": "Welcome to ProfileForge! Navigate to http://127.0.0.1:10000/docs for the interactive Swagger UI.",
    }


# Health & Diagnostics Endpoints
@app.get("/healthz", tags=["Diagnostics"])
async def healthz() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok", "service": "profileforge", "version": "1.0.0"}


@app.get("/readyz", tags=["Diagnostics"])
async def readyz() -> dict[str, str]:
    """Readiness probe evaluating cache and service health."""
    stats = await cache_instance.get_stats()
    return {
        "status": "ready",
        "extractor": settings.EXTRACTOR_TYPE,
        "cache_entries": str(stats["size"]),
    }


# Core Lookup Endpoint
@app.post(
    "/v1/profile",
    response_model=ProfileLookupResponse,
    status_code=status.HTTP_200_OK,
    tags=["Profile Lookup"],
    summary="Lookup LinkedIn Profile",
    description="Accepts a LinkedIn profile URL, fetches structured data, and returns normalized JSON with quality metrics.",
)
async def lookup_profile(
    body: ProfileLookupRequest,
    request: Request,
    _: str = Depends(rate_limit_dependency),
) -> ProfileLookupResponse:
    """Primary profile lookup route protected by API key and rate limiting."""
    request_id = getattr(request.state, "request_id", "req-unknown")
    return await profile_service.lookup(body.url, request_id=request_id)
