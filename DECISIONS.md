# ProfileForge — Architecture Decision Records (ADRs)

## D01: Extraction Strategy — Direct Browserless LinkedIn HTTP (Voyager REST)
- **Status**: Accepted (Supersedes LinkedAPI cloud-browser approach)
- **Context**: Tross challenge requirements specify that the final implementation must directly hit LinkedIn HTTP endpoints without browser emulation or third-party cloud-browser services.
- **Decision**: Reverse-engineer LinkedIn's internal Rest.li Voyager API (`/voyager/api/identity/dash/profiles`). Authenticate via session cookies (`li_at`, `JSESSIONID`), derive `csrf-token` header, and communicate over `httpx.AsyncClient` with connection pooling.
- **Consequences**: Pure HTTP architecture with sub-second upstream latency, zero browser overhead, zero Node.js runtime dependencies, and precise challenge/rate-limit detection.

---

## D02: Python Runtime Target — Python 3.12+
- **Status**: Accepted
- **Context**: Need maximum stability, predictable async performance, and mature library support.
- **Decision**: Standardize on Python 3.12+ for development, CI testing, and container deployment.

---

## D03: Response Schema & Objective DataQuality Model
- **Status**: Accepted
- **Context**: Profile data quality must be objective and relative to provider capabilities.
- **Decision**: Use `ProviderCapabilities` to calculate completeness ratio $\text{score} = \frac{|\text{available}|}{|\text{supported}|}$. Supported sections evaluate into `available` or `missing`, unsupported into `unavailable`, and schema failures into `parser_failed`.

---

## D04: Layered Provider Adapter Architecture
- **Status**: Accepted
- **Context**: Upstream provider structures and protocol quirks must remain strictly encapsulated.
- **Decision**: Four-stage adapter pipeline: `LinkedInClient` $\rightarrow$ `LinkedInParser` $\rightarrow$ `LinkedInResolver` $\rightarrow$ `LinkedInNormalizer`.

---

## D05: Cache Strategy — Canonical Profile Identifier Key
- **Status**: Accepted
- **Context**: Repeated queries for the same profile (across URL variations) should respond in sub-10ms.
- **Decision**: In-memory cache keyed by provider plus canonical profile slug (for example, `linkedin_direct:sarah-jenkins-dev`) with configurable TTL (default: 3600s). This prevents mock data from being served after switching providers in the same process.

---

## D06: Application Concurrency Guard
- **Status**: Accepted
- **Context**: Downstream burst traffic must not overload single-account upstream quotas.
- **Decision**: Wrap extraction calls in `asyncio.Semaphore` with `MAX_CONCURRENT_EXTRACTIONS=2` (configurable).

---

## D07: Standardized Error Taxonomy
- **Status**: Accepted
- **Context**: Translates upstream errors, timeouts, and challenge states into stable application-level codes.
- **Decision**: Standard `ErrorCode` enum mapping cleanly to standard HTTP status codes (400, 401, 404, 429, 502, 503, 504).

---

## D08: Production Container Runtime — `python:3.12-slim`
- **Status**: Accepted
- **Context**: Eliminate browser and Node.js runtime bloat and keep image size minimal.
- **Decision**: Use `python:3.12-slim` (~130MB) running as non-privileged `appuser`.

---

## D09: Strict URL Validation & SSRF Guard
- **Status**: Accepted
- **Context**: Untrusted URLs must not allow SSRF attacks against internal network hosts or cloud metadata endpoints.
- **Decision**: Enforce strict regex matching (`^/in/[a-zA-Z0-9_\-\%]+/?$`), exact hostname allowlists, and IP blocking for RFC 1918, RFC 3927 (AWS/GCP metadata `169.254.169.254`), and IPv6 loopback.

---

## D10: Single-Flight Request Coalescing
- **Status**: Accepted
- **Context**: High-concurrency duplicate requests for the same uncached profile would cause redundant upstream calls and race conditions.
- **Decision**: Coordinate concurrent queries using `asyncio.Future` in `ProfileService` so the first worker fetches while concurrent callers await the shared result.

---

## D11: Complete Elimination of Insecure Credential Modification Endpoints
- **Status**: Accepted
- **Context**: Public endpoints that write to `.env` or accept session tokens via HTTP requests represent severe security vulnerabilities.
- **Decision**: Eliminate all runtime credential-writing endpoints (`POST /v1/config/credentials`). Decouple client authentication (`X-API-Key`) completely from provider session tokens (`LINKEDIN_LI_AT`). Session tokens are exclusively supplied via secure server environment variables.
