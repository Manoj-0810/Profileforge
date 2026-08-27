# ProfileForge — Architecture Decision Records (ADRs)

## D01: Extraction Strategy — LinkedAPI REST Workflow API (Async Polling)
- **Status**: Accepted
- **Context**: Real-time profile lookups must be performed safely without ToS-violating direct browser scraping.
- **Decision**: Use LinkedAPI REST interface (`POST /workflows` + poll `GET /workflows/{id}`).
- **Consequences**: Pure Python HTTP implementation with asynchronous state machine, terminal failure short-circuiting, and polling deadlines.

---

## D02: Python Runtime Target — Python 3.12
- **Status**: Accepted
- **Context**: Need maximum stability, predictable async performance, and mature binary wheels.
- **Decision**: Standardize on Python 3.12 for development, CI testing, and container deployment.

---

## D03: Response Schema & Provider-Aware Data Quality Model
- **Status**: Accepted
- **Context**: Profiling data quality must be objective and relative to provider capabilities.
- **Decision**: Use `ProviderCapabilities` to calculate completeness ratio $S = \frac{|A \cap C|}{|C|}$. Supported sections evaluate into `available` or `missing`, unsupported sections evaluate into `unavailable`, and schema failures evaluate into `parser_failed`.

---

## D04: Layered Provider Adapter Architecture
- **Status**: Accepted
- **Context**: Upstream provider structures must remain strictly encapsulated.
- **Decision**: Four-stage adapter pipeline: Client -> Parser -> Resolver -> Normalizer.

---

## D05: Cache Strategy — Canonical Profile Identifier Key
- **Status**: Accepted
- **Context**: Profile fetches take 30s-60s; repeated queries must respond under 10ms.
- **Decision**: In-memory cache keyed by canonical profile slug with configurable TTL (default: 3600s).

---

## D06: Application Concurrency Guard
- **Status**: Accepted
- **Context**: Downstream burst traffic must not overload single-account upstream quotas.
- **Decision**: Wrap extraction calls in `asyncio.Semaphore` with `MAX_CONCURRENT_EXTRACTIONS=2` (configurable).

---

## D07: Standardized Error Taxonomy
- **Status**: Accepted
- **Context**: Translates upstream errors, timeouts, and account issues into stable application-level codes.
- **Decision**: Standard `ErrorCode` enum mapping cleanly to standard HTTP status codes (400, 401, 404, 429, 502, 503, 504).

---

## D08: Production Container Runtime — `python:3.12-slim`
- **Status**: Accepted
- **Context**: Eliminate Node.js runtime bloat and keep image size minimal.
- **Decision**: Use `python:3.12-slim` (~130MB) running as non-root `appuser`.

---

## D09: Strict URL Validation & SSRF Guard
- **Status**: Accepted
- **Context**: Profile URLs are untrusted input.
- **Decision**: Restrict hostnames to `linkedin.com` / `www.linkedin.com`, path to `/in/<id>`, and block private/loopback IP ranges.

---

## D10: Multi-Layered Testing with Offline Provider Contracts
- **Status**: Accepted
- **Context**: Ensure offline, deterministic CI/CD execution.
- **Decision**: Test against sanitized JSON fixtures in `tests/contract/` and `tests/unit/`.

---

## D11: Deployment Target & Environment Variables
- **Status**: Accepted
- **Context**: Containerized public HTTPS deployment.
- **Decision**: Deploy via Docker to Render.com with environment variables and `DEPLOYED_BASE_URL` placeholder.

---

## D12: Restrictive CORS Policy
- **Status**: Accepted
- **Context**: Avoid open `*` wildcards on server-to-server APIs.
- **Decision**: Configurable `CORS_ORIGINS` defaulting to empty/restricted.

---

## D13: ProviderCapabilities Abstraction
- **Status**: Accepted
- **Context**: Different providers expose different subsets of profile fields.
- **Decision**: Introduce `ProviderCapabilities` declaring `supported_sections` and `unsupported_sections` to decouple domain quality scoring from specific provider quirks.

---

## D14: Explicit Retry & Backoff Policy
- **Status**: Accepted
- **Context**: Prevent retry storms while gracefully recovering from transient network blips.
- **Decision**: Exponential backoff with jitter for network/5xx transient errors (max 2-3 attempts); zero retries for 4xx, auth, rate limits, or account signouts.

---

## D15: Single-Flight Duplicate Request Protection
- **Status**: Accepted
- **Context**: Concurrent requests for the same uncached profile ID must not trigger duplicate upstream workflows.
- **Decision**: Request coalescing in `ProfileService` using `dict[str, asyncio.Future[ProfileData]]`.
