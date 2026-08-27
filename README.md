# ProfileForge — Production Profile Lookup API

[![CI Pipeline](https://github.com/profileforge/profileforge/actions/workflows/ci.yml/badge.svg)](https://github.com/profileforge/profileforge)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> High-reliability, provider-isolated Profile Lookup API engineered for the **Tross Software Engineer Hiring Challenge**.

---

## 1. Executive Summary

**ProfileForge** accepts public LinkedIn profile URLs, executes bounded upstream workflow extraction via authorized account credentials, enforces strict SSRF protections and single-flight request coalescing, and delivers normalized JSON data with deterministic, provider-aware completeness scores in sub-10ms for cached lookups.

### Key Architectural Highlights
- **Layered Provider Isolation**: Four-stage adapter pipeline (`Client` $\rightarrow$ `Parser` $\rightarrow$ `Resolver` $\rightarrow$ `Normalizer`) encapsulating all third-party quirks.
- **ProviderCapabilities Abstraction**: Dynamic capability declarations decoupling domain quality assessment from provider feature sets.
- **Single-Flight Coalescing**: Duplicate concurrent queries for the same profile ID merge into a single in-flight upstream workflow.
- **Strict Security & SSRF Defenses**: Hostname allowlisting, path normalization, private/loopback IP blocking, constant-time API key verification, and automated secret log redaction.
- **Deterministic Offline Testing**: 81 comprehensive unit, integration, and contract tests running 100% offline with 88% statement coverage.

---

## 2. API Specification & Endpoints

### 2.1 Base URL
- **Production Endpoint**: `https://DEPLOYED_BASE_URL` *(Configured via Render.com / Cloud Provider)*
- **Local Dev Server**: `http://localhost:10000`

### 2.2 Endpoints Overview

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/profile` | `X-API-Key` | Lookup and normalize LinkedIn profile |
| `GET` | `/healthz` | No | Liveness probe for load balancers |
| `GET` | `/readyz` | No | Readiness probe reporting cache & provider health |
| `GET` | `/docs` | No | Interactive OpenAPI Swagger documentation |

---

## 3. Example Request & Response Contract

### 3.1 Request

```bash
curl -X POST "http://localhost:10000/v1/profile" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"url": "https://www.linkedin.com/in/sarah-jenkins-dev"}'
```

### 3.2 Success Response (`HTTP 200 OK`)

```json
{
  "profile": {
    "full_name": "Sarah Jenkins",
    "headline": "Staff Distributed Systems Engineer @ CloudScale",
    "location": "Seattle, Washington, United States",
    "country_code": "US",
    "about": "Passionate backend engineer specializing in high-throughput streaming systems.",
    "profile_image_url": "https://media.licdn.com/dms/image/v2/example.jpg",
    "profile_url": "https://www.linkedin.com/in/sarah-jenkins-dev",
    "canonical_url": "https://www.linkedin.com/in/sarah-jenkins-dev",
    "urn": "urn:li:member:849201948",
    "current_position": "Staff Distributed Systems Engineer",
    "current_company": "CloudScale Inc.",
    "followers_count": 4510,
    "experience": [
      {
        "title": "Staff Distributed Systems Engineer",
        "company": "CloudScale Inc.",
        "company_url": "https://www.linkedin.com/company/92847192",
        "employment_type": "fullTime",
        "location_type": "hybrid",
        "description": "Architecting multi-region streaming pipelines handling 5M events/sec.",
        "duration_months": 28,
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": null,
        "location": "Seattle, WA"
      }
    ],
    "education": [
      {
        "school": "University of Washington",
        "school_url": "https://www.linkedin.com/company/uw1861",
        "details": "Master of Science in Computer Science & Engineering",
        "degree": "Master of Science",
        "field_of_study": "Computer Science & Engineering",
        "start_date": "2018-09-01T00:00:00Z",
        "end_date": "2020-06-15T00:00:00Z"
      }
    ],
    "skills": ["Distributed Systems", "Python", "Go", "Kubernetes", "FastAPI"],
    "certifications": [],
    "languages": [
      { "name": "English", "proficiency": "Native or bilingual" },
      { "name": "German", "proficiency": "Professional working" }
    ]
  },
  "fetched_at": "2026-08-27T13:20:00Z",
  "cache_hit": false,
  "source": "linkedapi",
  "request_id": "9f24b2a8-3482-4f3b-81ae-2819a048d821",
  "data_quality": {
    "available_sections": ["full_name", "headline", "location", "experience", "education", "skills", "languages", "about", "profile_image_url"],
    "missing_sections": [],
    "unavailable_sections": ["certifications"],
    "parser_failed_sections": [],
    "completeness_score": 1.0
  }
}
```

### 3.3 Standardized Error Response (`HTTP 4xx / 5xx`)

```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "Upstream profile lookup timed out after 120.0s.",
    "request_id": "9f24b2a8-3482-4f3b-81ae-2819a048d821"
  }
}
```

---

## 4. Architecture & System Flow

```mermaid
graph TD
    Client["API Consumer"]
    
    subgraph FastAPI HTTP Application Layer
        ReqID["Request ID Middleware"]
        LoggingMW["Structured Logging & Header Redaction"]
        AuthMW["API Key Authentication (X-API-Key)"]
        RateLimitMW["Sliding Window Rate Limiter"]
    end
    
    subgraph Core Domain & Security Layer
        URLVal["URL Validator & SSRF Guard"]
        ProfileSvc["ProfileService (SingleFlight)"]
        Cache["InMemoryCache (Key: Canonical Profile ID)"]
        Sem["Concurrency Semaphore (MAX_CONCURRENT_EXTRACTIONS=2)"]
    end
    
    subgraph Provider Adapter Layer (app/providers/linkedapi)
        ExtIF["ProfileExtractor Protocol"]
        LinkedInExt["LinkedInExtractor"]
        ClientHTTP["LinkedAPIClient (HTTP Submit + Poll + Backoff)"]
        Parser["LinkedAPIParser (Schema Validation)"]
        Resolver["LinkedAPIResolver (URN & Entity Index)"]
        Normalizer["LinkedAPINormalizer (DataQuality & Domain Map)"]
    end
    
    subgraph Upstream Service
        RemoteAPI["LinkedAPI Remote API (api.linkedapi.io)"]
    end

    Client -->|HTTPS Request| ReqID
    ReqID --> LoggingMW
    LoggingMW --> AuthMW
    AuthMW --> RateLimitMW
    RateLimitMW --> URLVal
    URLVal --> ProfileSvc
    ProfileSvc --> Cache
    Cache -->|Cache HIT <10ms| Client
    Cache -->|Cache MISS| Sem
    Sem --> ExtIF
    ExtIF --> LinkedInExt
    LinkedInExt --> ClientHTTP
    ClientHTTP -->|POST /workflows & GET poll| RemoteAPI
    ClientHTTP --> Parser
    Parser --> Resolver
    Resolver --> Normalizer
    Normalizer --> ProfileSvc
    ProfileSvc --> Cache
```

---

## 5. Extraction Approach & Provider Decision

### 5.1 Evaluated Approaches
1. **Official LinkedIn API**: Restricted to enterprise partner contracts (Talent Solutions / Marketing); does not allow arbitrary developer profile lookups.
2. **Voyager API with Session Cookies (`li_at`)**: Highly brittle, violates LinkedIn ToS, triggers automated anti-bot bans (Spectroscopy).
3. **Legacy Scraping Proxies (Proxycurl)**: Defunct post-2025 legal actions.
4. **LinkedAPI REST Workflow API**: Account-based automation using cloud-browser simulation on behalf of the developer's authorized LinkedIn account. **Selected**.

### 5.2 Provider Isolation Architecture
The core domain model never references LinkedAPI structures. All communication is encapsulated in `app/providers/linkedapi/`:
- `client.py`: Submits workflows via `POST /workflows`, polls `GET /workflows/{id}` with exponential backoff and jitter, short-circuits on terminal failures (`linkedinAccountSignedOut`, `outsideWorkingHours`), and cancels workflows on timeout.
- `parser.py`: Performs structural validation, detecting schema drift without discarding uncorrupted fields.
- `resolver.py`: Resolves URN entities, normalizes institution names, and parses degrees and majors via regex pattern matching.
- `normalizer.py`: Transforms intermediate records into `ProfileData` and evaluates `DataQuality` against declared `ProviderCapabilities`.

---

## 6. Security & Operational Reliability

| Guard | Implementation | Impact |
| :--- | :--- | :--- |
| **SSRF Defense** | `app/services/url_utils.py` | Blocks loopback, private IPv4/IPv6 ranges, and non-LinkedIn hostnames |
| **Single-Flight Coalescing** | `app/services/profile_service.py` | Coalesces concurrent identical requests into one in-flight upstream job |
| **Bounded Concurrency** | `asyncio.Semaphore` | Limits simultaneous upstream extractions to configurable quota (default: 2) |
| **Sliding Window Limiter** | `app/rate_limit.py` | Protects server from abuse; returns `429` with `Retry-After` headers |
| **Log Sanitization** | `app/logging_config.py` | Automatically redacts `x-api-key`, `linked-api-token`, and authorization headers |
| **Non-Root Container** | `Dockerfile` | Runs as unprivileged `appuser` on minimal `python:3.12-slim` image |

---

## 7. Testing & Quality Gates

The test suite runs 100% offline in CI and covers unit, integration, and provider contract tests.

```bash
# Run full offline test suite with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run static type checking
mypy app/

# Run linter and code formatter
ruff check app tests
ruff format --check app tests
```

### Test Suite Structure
- `tests/unit/`: Tests models, URL parsing, cache TTL, rate limiting, auth, client state machine, single-flight coalescer, parser, resolver, and normalizer.
- `tests/contract/`: Tests 13 raw upstream fixtures against parser/normalizer pipeline and asserts schema drift behavior.
- `tests/integration/`: Tests end-to-end FastAPI HTTP pipeline, cache-hit equivalence across URL variations, diagnostics, and error envelopes.
- `tests/e2e/`: Conditional live smoke test executed only when real upstream tokens are configured.

---

## 8. Deployment Guide (Render.com)

### 8.1 Docker Deployment
The repository includes a production-ready `Dockerfile` and `render.yaml` blueprint.

1. Create a new Web Service on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Select **Docker** environment.
4. Configure environment variables:
   - `PORT`: `10000`
   - `ENVIRONMENT`: `production`
   - `EXTRACTOR_TYPE`: `linkedapi` (or `mock`)
   - `API_KEYS`: `your-secure-client-api-key`
   - `LINKEDAPI_TOKEN`: `your-linkedapi-developer-token`
   - `LINKEDAPI_IDENTIFICATION_TOKEN`: `your-linkedapi-session-token`

---

## 9. Known Limitations & Transparency

1. **Certifications Availability**: Documented finding: Certifications are not exposed in LinkedAPI's primary standard action set (`st.retrieve*`). Handled gracefully in domain models as an empty list and tracked in `unavailable_sections`.
2. **Upstream Latency**: Natural cloud-browser emulation takes 30s–60s per uncached profile fetch. Mitigated by in-memory caching and single-flight request coalescing.
3. **Sequential Execution per Account**: LinkedAPI queues workflows sequentially for a given LinkedIn account. Bounded by the application concurrency semaphore (`MAX_CONCURRENT_EXTRACTIONS=2`).
