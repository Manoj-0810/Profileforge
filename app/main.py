"""Main FastAPI application entry point for ProfileForge."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import Body, Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.cache import InMemoryCache
from app.config import settings
from app.errors import ErrorCode, ProfileForgeError
from app.extractor.base import ProfileExtractor
from app.extractor.linkedin_direct import DirectLinkedInExtractor
from app.extractor.mock import MockExtractor
from app.logging_config import RequestLoggingMiddleware, setup_logging
from app.models import (
    ErrorDetails,
    ErrorResponse,
    ProfileLookupRequest,
    ProfileLookupResponse,
)
from app.providers.linkedin.client import LinkedInClient
from app.rate_limit import rate_limit_dependency
from app.services.profile_service import ProfileService
from app.ui import HTML_PLAYGROUND

logger = structlog.get_logger(__name__)

# Global cache and direct HTTP client instances
cache_instance = InMemoryCache(default_ttl_seconds=settings.CACHE_TTL_SECONDS)
linkedin_http_client: LinkedInClient | None = None


def create_profile_service() -> ProfileService:
    """Factory creating ProfileService configured for the active environment."""
    global linkedin_http_client
    extractor: ProfileExtractor

    if settings.EXTRACTOR_TYPE == "linkedin":
        linkedin_http_client = LinkedInClient(
            li_at=settings.LINKEDIN_LI_AT,
            jsessionid=settings.LINKEDIN_JSESSIONID,
            user_agent=settings.LINKEDIN_USER_AGENT,
            proxy_url=settings.LINKEDIN_PROXY_URL,
            timeout_seconds=settings.UPSTREAM_TIMEOUT_SECONDS,
        )
        extractor = DirectLinkedInExtractor(client=linkedin_http_client)
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
    settings.validate_runtime_configuration()
    setup_logging(environment=settings.ENVIRONMENT)
    logger.info(
        "server_startup",
        environment=settings.ENVIRONMENT,
        extractor_type=settings.EXTRACTOR_TYPE,
        max_concurrency=settings.MAX_CONCURRENT_EXTRACTIONS,
    )
    yield
    await cache_instance.clear()
    if linkedin_http_client is not None:
        await linkedin_http_client.close()
    logger.info("server_shutdown")


app = FastAPI(
    title="ProfileForge API",
    description="High-reliability Profile Lookup API returning normalized LinkedIn profile data via direct HTTP communication.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Attach Structured Logging & Traceability Middleware
app.add_middleware(RequestLoggingMiddleware)

# Secure CORS Middleware (Enabled only if explicit origins configured)
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


# Standardized Exception Handlers
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
            message="The request body is invalid. Provide a LinkedIn profile URL in the 'url' field.",
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


# Root Visual Playground
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> HTMLResponse:
    """Interactive visual playground and developer console."""
    return HTMLResponse(content=HTML_PLAYGROUND)


# Diagnostics Endpoints
@app.get("/healthz", tags=["Diagnostics"])
async def healthz() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok", "service": "profileforge", "version": "1.0.0"}


@app.get("/readyz", tags=["Diagnostics"])
async def readyz() -> JSONResponse:
    """Readiness probe evaluating cache and service health."""
    stats = await cache_instance.get_stats()
    provider_configured = settings.EXTRACTOR_TYPE == "mock" or bool(
        settings.LINKEDIN_LI_AT.strip() and settings.LINKEDIN_JSESSIONID.strip()
    )
    payload = {
        "status": "ready" if provider_configured else "not_ready",
        "extractor": settings.EXTRACTOR_TYPE,
        "provider_configured": provider_configured,
        "cache_entries": str(stats["size"]),
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK
        if provider_configured
        else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )


# Core Lookup Endpoint
@app.post(
    "/v1/profile",
    response_model=ProfileLookupResponse,
    status_code=status.HTTP_200_OK,
    tags=["Profile Lookup"],
    summary="Lookup LinkedIn Profile",
    description="Accepts a LinkedIn profile URL, fetches structured data directly over HTTP, and returns normalized JSON.",
    responses={
        status.HTTP_200_OK: {
            "model": ProfileLookupResponse,
            "description": "Successful profile lookup returning structured normalized JSON",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid LinkedIn profile URL or unsupported hostname",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed: Missing or invalid ProfileForge API key ('X-API-Key' header)",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Profile not found on LinkedIn",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Client rate limit exceeded (Retry-After header included)",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "Upstream LinkedIn error, rate limit, anti-bot challenge, or schema change",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": ErrorResponse,
            "description": "Upstream LinkedIn request timed out",
        },
    },
)
async def lookup_profile(
    request: Request,
    body: ProfileLookupRequest = Body(  # noqa: B008
        openapi_examples={
            "default": {
                "summary": "Standard Profile Lookup",
                "description": "Standard profile lookup with default caching behavior",
                "value": {
                    "url": "https://www.linkedin.com/in/sarah-jenkins-dev",
                    "bypass_cache": False,
                },
            },
            "bypass_cache": {
                "summary": "Force Live Lookup",
                "description": "Force fresh live extraction bypassing cache",
                "value": {
                    "url": "https://www.linkedin.com/in/sarah-jenkins-dev",
                    "bypass_cache": True,
                },
            },
        }
    ),
    api_key: str = Depends(rate_limit_dependency),
) -> ProfileLookupResponse:
    """Primary profile lookup route protected by API key and rate limiting."""
    request_id = getattr(request.state, "request_id", "req-unknown")
    return await profile_service.lookup(
        body.url,
        request_id=request_id,
        bypass_cache=body.bypass_cache,
    )
