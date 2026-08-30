# ProfileForge — Repository Audit & Security Assessment

**Audit Date**: 2026-08-29  
**Target Context**: Tross Software Engineer Hiring Challenge — Direct Browserless LinkedIn HTTP Migration  
**Auditor**: Principal Backend & Security Engineering Review  

> Historical baseline audit. The remediation and migration actions described
> below are complete in the current working tree; use the current source,
> `README.md`, and `TEST_REPORT.md` as the authoritative state.

---

## 1. Executive Summary

ProfileForge was previously constructed around an asynchronous polling workflow integration with LinkedAPI. Following the updated Tross technical requirement, the LinkedIn extraction path must be **purely reverse-engineered, browserless, and directly interact with LinkedIn HTTP endpoints**.

This audit details:
1. **Reusable Core Architecture**: 85%+ of the existing application core is well-engineered and provider-agnostic (FastAPI server, `ProfileExtractor` Protocol, `ProfileService` with single-flight request coalescing and concurrency semaphores, `InMemoryCache` with TTL, `SlidingWindowRateLimiter`, constant-time API-key auth, Pydantic v2 schemas, SSRF URL validation, and structured telemetry).
2. **Provider-Coupled Code**: The entire `app/providers/linkedapi/` package, `app/extractor/linkedin.py`, and LinkedAPI configuration must be decoupled and replaced with a direct LinkedIn HTTP provider (`app/providers/linkedin/`).
3. **Security Vulnerabilities (Must Remediate First)**: Unauthenticated credential mutation endpoints (`POST /v1/config/credentials`), secret discovery routes (`GET /v1/config/status`), trust domain conflation in `app/auth.py`, and permissive CORS wildcard defaults.
4. **Testing Suite**: 12 core test suites are 100% provider-independent and retained; 7 provider/contract suites must be re-anchored to direct LinkedIn HTTP contracts with sanitized offline fixtures.

---

## 2. Component Reusability Matrix

| Module | Location | Status | Action Required |
| :--- | :--- | :--- | :--- |
| **HTTP Framework & Routing** | `app/main.py` | 75% Reusable | Remove `/v1/config/credentials`, `/v1/config/status`, `/v1/cache/clear`. Fix CORS middleware. Wire direct LinkedIn extractor into DI. |
| **Domain Models & Schemas** | `app/models.py` | 95% Reusable | Provider-independent Pydantic v2 models (`ProfileData`, `ExperienceEntry`, etc.). Make `source` default dynamic; update capabilities. |
| **Extractor Protocol** | `app/extractor/base.py` | 100% Reusable | Clean `@runtime_checkable` `ProfileExtractor` protocol (`capabilities`, `fetch(url)`). Keep as-is. |
| **Mock Extractor** | `app/extractor/mock.py` | 80% Reusable | Decouple from `app.providers.linkedapi` imports. Provide deterministic multi-scenario mock data (complete, partial, minimal). |
| **URL Validator & SSRF Guard** | `app/services/url_utils.py` | 100% Reusable | Production-grade regex parsing, canonical slug extraction, and comprehensive RFC 1918 / RFC 3927 / IPv6 loopback blocking. |
| **Profile Service & Orchestrator** | `app/services/profile_service.py` | 85% Reusable | Single-flight request coalescing (`asyncio.Future`) and concurrency semaphore. Remove LinkedAPI normalizer import. |
| **Caching Backend** | `app/cache.py` | 100% Reusable | `CacheBackend` protocol + thread-safe `InMemoryCache` with TTL, deletion, and hit/miss statistics. |
| **Authentication Middleware** | `app/auth.py` | 85% Reusable | Constant-time comparison (`secrets.compare_digest`). Remove `LINKEDAPI_TOKEN` fallback. |
| **Rate Limiter** | `app/rate_limit.py` | 100% Reusable | Sliding-window counter tracking per-key quotas with `Retry-After` headers. |
| **Error Taxonomy** | `app/errors.py` | 100% Reusable | `ErrorCode` enum with deterministic HTTP status mapping and `ProfileForgeError` class. |
| **Structured Logging** | `app/logging_config.py` | 90% Reusable | JSON / console structured logger with request ID tracing context. Add session cookies (`li_at`, `JSESSIONID`) to `SENSITIVE_HEADERS`. |
| **Web UI Playground** | `app/ui.py` | 70% Reusable | Keep profile lookup, response viewer, data quality badges, latency meters. Remove all credential-entry and config-write forms. |
| **LinkedAPI Provider** | `app/providers/linkedapi/` | 0% (Obsolete) | Remove from runtime path. Archive research notes in `docs/archive/`. |
| **Direct LinkedIn Provider** | `app/providers/linkedin/` | New | Implement direct HTTP client, request builder, parser, entity resolver, normalizer. |

---

## 3. Security Vulnerability Inventory (Remediation Priority 1)

### 🔴 Vulnerability 1: Unauthenticated Credential Overwrite & Key Exfiltration
- **Affected Route**: `POST /v1/config/credentials` (`app/main.py:L226-L248`, `app/config.py:L115-L161`)
- **Severity**: CRITICAL
- **Description**: Endpoint lacks authentication (`verify_api_key` omitted). Any anonymous client can overwrite `.env` on disk and retrieve all configured API keys in the response body (`"api_keys": settings.API_KEYS`).
- **Remediation**: Eliminate this route and the `save_env_credentials()` helper completely. Credentials must be managed exclusively via server environment variables.

### 🔴 Vulnerability 2: Unauthenticated Configuration Discovery
- **Affected Route**: `GET /v1/config/status` and `POST /v1/cache/clear` (`app/main.py:L213-L224`, `L250-L255`)
- **Severity**: HIGH
- **Description**: `GET /v1/config/status` exposes mock API keys anonymously. `POST /v1/cache/clear` allows unauthenticated cache flushes, exposing upstream services to cache-stampede DoS.
- **Remediation**: Remove status route or protect under strict admin auth; delete unauthenticated cache clear route.

### 🟡 Vulnerability 3: Upstream Credential Trust Domain Conflation
- **Affected File**: `app/auth.py:L42-L44`
- **Severity**: HIGH
- **Description**: `valid_keys.append(settings.LINKEDAPI_TOKEN)` allows upstream service tokens to act as downstream client API keys.
- **Remediation**: Completely decouple client API key verification from provider session secrets.

### 🟡 Vulnerability 4: CORS Wildcard with Allowed Credentials
- **Affected File**: `app/main.py:L91-L98`
- **Severity**: MEDIUM
- **Description**: `allow_origins=["*"]` is combined with `allow_credentials=True` when `CORS_ORIGINS` is not set.
- **Remediation**: When `CORS_ORIGINS` is empty, disable CORS or restrict to explicit non-wildcard origins.

---

## 4. Test Suite Audit

### 4.1 Retained Tests (100% Provider-Independent)
- `tests/unit/test_url_utils.py`: URL parsing, slug extraction, SSRF IP blocking.
- `tests/unit/test_cache.py`: Cache hits, misses, TTL expiry, deletion.
- `tests/unit/test_rate_limiter.py`: Sliding window quota, 429 response, Retry-After.
- `tests/unit/test_single_flight.py`: Concurrency coalescing via `asyncio.Future`.
- `tests/unit/test_models.py`: Pydantic v2 schemas and validation.
- `tests/unit/test_errors.py`: Error code enum to HTTP status mappings.
- `tests/unit/test_auth.py`: API key header verification and rejection.
- `tests/unit/test_secret_leakage.py`: Repository secret scanner.
- `tests/integration/test_api_flow.py`: End-to-end `/v1/profile` flow.
- `tests/integration/test_cache_behavior.py`: Canonical URL caching equivalence.
- `tests/integration/test_diagnostics.py`: `/healthz` and `/readyz` probes.
- `tests/integration/test_error_responses.py`: Error response envelope uniformity.

### 4.2 Tests Requiring Migration (LinkedAPI-Specific)
- `tests/unit/test_linkedapi_client.py` ➔ Migrate to `tests/unit/test_linkedin_client.py` (direct HTTP, session cookies, status handling, challenge detection).
- `tests/unit/test_parser.py` ➔ Migrate to `tests/unit/test_linkedin_parser.py` (Voyager/direct response parsing).
- `tests/unit/test_resolver.py` ➔ Migrate to `tests/unit/test_linkedin_resolver.py` (entity reference index and URN resolution).
- `tests/unit/test_normalizer.py` ➔ Migrate to `tests/unit/test_linkedin_normalizer.py` (direct data normalization).
- `tests/contract/test_provider_contract.py` ➔ Migrate to `tests/contract/test_voyager_contract.py` (sanitized direct LinkedIn JSON fixtures).
- `tests/contract/test_schema_drift.py` ➔ Migrate to test direct LinkedIn schema drift and HTTP 999 challenges.
- `tests/e2e/test_live_smoke.py` ➔ Migrate to live direct HTTP smoke test (conditional on environment credentials).

### 4.3 Missing Security Tests (To Add)
- `tests/security/test_endpoint_auth.py`: Dynamically enumerates all registered FastAPI routes and asserts that all non-health endpoints require valid authentication, rejecting missing/invalid credentials.

---

## 5. Configuration & Deployment Audit

- **`Dockerfile`**: Minimal single-stage container using `python:3.12-slim` and non-root `appuser`. Production-ready.
- **`render.yaml`**: Web service Blueprint for Render. Needs update to replace LinkedAPI environment variables with direct LinkedIn session variables.
- **`.env.example`**: Clean template without real secrets; needs update for direct LinkedIn configuration.
- **`.gitignore`**: Properly excludes `.env`, `*.env.local`, `.coverage`, caches, and build artifacts.
- **CI (`.github/workflows/ci.yml`)**: Multi-job CI enforcing Ruff linting, Mypy type-checking, Pytest coverage (>=85%), container build, and secret scanning.

---

## 6. Migration Action Plan Reference

The complete sequence of execution steps is detailed in [`MIGRATION_PLAN.md`](./MIGRATION_PLAN.md).
Security remediation (Phase 1) will be executed immediately before provider implementation (Phase 2).
