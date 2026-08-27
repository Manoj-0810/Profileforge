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
from pydantic import BaseModel, Field

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
    if settings.EXTRACTOR_TYPE == "linkedapi" and settings.LINKEDAPI_TOKEN:
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
    """Application lifecycle hook for resource initialization and teardown."""
    setup_logging(environment=settings.ENVIRONMENT)
    logger.info(
        "server_startup",
        environment=settings.ENVIRONMENT,
        extractor_type=settings.EXTRACTOR_TYPE,
        max_concurrency=settings.MAX_CONCURRENT_EXTRACTIONS,
    )
    yield
    await cache_instance.clear()
    logger.info("server_shutdown")


app = FastAPI(
    title="ProfileForge API",
    description="High-reliability Profile Lookup API returning normalized LinkedIn profile data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Attach Security & Operational Middleware
app.add_middleware(RequestLoggingMiddleware)

# Restrictive CORS middleware
allowed_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(ProfileForgeError)
async def handle_profile_forge_error(
    request: Request, exc: ProfileForgeError
) -> JSONResponse:
    """Handle domain ProfileForgeError exceptions with standardized error envelope."""
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
    """Handle FastAPI / Pydantic validation errors with 400 Bad Request."""
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorResponse(
        error=ErrorDetails(
            code=ErrorCode.INVALID_PROFILE_URL.value,
            message=f"Validation failed: {exc.errors()}",
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_payload.model_dump(),
        headers={"X-Request-ID": request_id} if request_id else {},
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all unhandled exception handler ensuring zero internal stack traces in response."""
    request_id = getattr(request.state, "request_id", None)
    logger.exception("unhandled_internal_error", request_id=request_id, error=str(exc))
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


from fastapi.responses import HTMLResponse
from app.ui import HTML_PLAYGROUND


# Root Playground Endpoint
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> HTMLResponse:
    """Interactive visual playground and developer console."""
    return HTMLResponse(content=HTML_PLAYGROUND)


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


# Configuration & Credentials Management Models & Endpoints
class CredentialUpdateRequest(BaseModel):
    """Payload for updating LinkedAPI credentials and persistent .env configuration."""

    linkedapi_token: str | None = Field(
        default=None, description="LinkedAPI developer token"
    )
    identification_token: str | None = Field(
        default=None, description="LinkedAPI session identification token"
    )
    api_key: str | None = Field(
        default=None, description="Client API key to authorize in X-API-Key header"
    )
    extractor_type: str | None = Field(
        default="linkedapi", description="'linkedapi' or 'mock'"
    )


@app.get("/v1/config/status", tags=["Configuration"])
async def get_config_status() -> dict[str, Any]:
    """Check active provider mode and whether live credentials are configured."""
    return {
        "extractor_type": settings.EXTRACTOR_TYPE,
        "has_linkedapi_token": bool(settings.LINKEDAPI_TOKEN),
        "has_identification_token": bool(settings.LINKEDAPI_IDENTIFICATION_TOKEN),
        "mock_keys_active": ["test-api-key-123", "forge-secret-dev"],
        "max_concurrent_extractions": settings.MAX_CONCURRENT_EXTRACTIONS,
    }


@app.post("/v1/config/credentials", tags=["Configuration"])
async def update_credentials(
    payload: CredentialUpdateRequest,
) -> dict[str, Any]:
    """Persist credentials to .env and immediately activate real-time fetching."""
    result = save_env_credentials(
        linkedapi_token=payload.linkedapi_token,
        identification_token=payload.identification_token,
        api_key=payload.api_key,
        extractor_type=payload.extractor_type,
    )
    logger.info(
        "credentials_updated_via_api",
        extractor_type=settings.EXTRACTOR_TYPE,
        has_token=bool(settings.LINKEDAPI_TOKEN),
    )
    return {
        "status": "success",
        "message": "Credentials successfully saved to .env and activated.",
        "config": result,
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
    api_key: str = Depends(rate_limit_dependency),
) -> ProfileLookupResponse:
    """Primary profile lookup route protected by API key and rate limiting.

    - Uses MockExtractor if test-api-key-123 or forge-secret-dev is used, or header X-Extractor-Mode: mock is set.
    - Uses live LinkedInExtractor if live LinkedAPI tokens are configured and a real or configured key is used.
    """
    request_id = getattr(request.state, "request_id", "req-unknown")
    header_mode = request.headers.get("X-Extractor-Mode", "").lower()

    # Determine dynamic extractor
    override_extractor: ProfileExtractor | None = None

    if header_mode == "mock" or api_key in ["test-api-key-123", "forge-secret-dev"]:
        # User requested mock data or entered default test key
        override_extractor = MockExtractor()
    elif settings.EXTRACTOR_TYPE == "linkedapi" or settings.LINKEDAPI_TOKEN:
        if not settings.LINKEDAPI_TOKEN or not settings.LINKEDAPI_IDENTIFICATION_TOKEN:
            raise ProfileForgeError(
                ErrorCode.AUTH_CONFIGURATION_ERROR,
                "LinkedAPI credentials incomplete. Please configure LINKEDAPI_TOKEN and LINKEDAPI_IDENTIFICATION_TOKEN in .env or via the playground.",
                status_code=503,
            )
        client = LinkedAPIClient(
            api_token=settings.LINKEDAPI_TOKEN,
            identification_token=settings.LINKEDAPI_IDENTIFICATION_TOKEN,
            timeout_seconds=settings.UPSTREAM_TIMEOUT_SECONDS,
            poll_interval_seconds=settings.LINKEDAPI_POLL_INTERVAL_SECONDS,
        )
        override_extractor = LinkedInExtractor(client=client)

    return await profile_service.lookup(
        body.url, request_id=request_id, override_extractor=override_extractor
    )
