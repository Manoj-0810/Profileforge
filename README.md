# ProfileForge — Browserless LinkedIn Profile Lookup API

[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> High-reliability, browserless direct HTTP Profile Lookup API engineered for the **Tross Software Engineer Hiring Challenge**.

---

## 1. What It Is

**ProfileForge** is an API-first developer service that accepts public LinkedIn profile URLs, communicates **directly with LinkedIn HTTP endpoints without a browser**, and returns rich, normalized, structured JSON data. Browser use is limited to the optional local playground; the LinkedIn acquisition path never launches, controls, or embeds a browser.

It features:
- **Zero Browser Dependencies**: Uses direct, reverse-engineered HTTP communication against LinkedIn's internal Rest.li Voyager protocol with session cookie authentication and CSRF token derivation.
- **Strict Separation of Concerns**: Multi-layered pipeline (`Client` $\rightarrow$ `Parser` $\rightarrow$ `Resolver` $\rightarrow$ `Normalizer`) isolating upstream protocol nuances from public domain schemas.
- **High Concurrency & Resilience**: Single-flight request coalescing (`asyncio.Future`), semaphore-bounded concurrency, persistent HTTP connection pooling, and in-memory TTL caching.
- **Enterprise-Grade Security**: Constant-time `X-API-Key` verification, strict SSRF guards blocking private/loopback IPs, automatic sensitive header log redaction, and total decoupling of public API auth from upstream session secrets.
- **Deterministic Multi-Layered Testing**: 88 automated unit, integration, security, and contract tests pass offline, with one conditional live smoke test and zero external network dependencies in CI.

---

## 2. Deployment & Playground

The service is deployment-ready for Render or any Docker-compatible host. After
deployment, verify the host before submitting it and add the real URL here:

- **Public HTTPS Base URL**: `https://profileforge-ysbd.onrender.com`
- **Interactive Web UI**: `https://profileforge-ysbd.onrender.com/`
- **Interactive OpenAPI Documentation**: `https://profileforge-ysbd.onrender.com/docs`
- **Health Check**: `https://profileforge-ysbd.onrender.com/healthz`

For local development, use `http://localhost:10000`.

---

## 3. Quick Start

### 3.1 Local Development (Python 3.12+)

```bash
# 1. Clone the public repository and navigate to directory
git clone https://github.com/Manoj-0810/Profileforge.git
cd profileforge

# 2. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Start local Uvicorn development server
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

Visit `http://localhost:10000` in your browser to access the visual developer playground.

### 3.2 Docker

```bash
# Build minimal production container
docker build -t profileforge .

# Run container on port 10000
docker run -p 10000:10000 --env-file .env profileforge
```

---

## 4. API Specification

### 4.1 Endpoints Overview

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/profile` | `X-API-Key` | Lookup and normalize LinkedIn profile data |
| `GET` | `/healthz` | No | Liveness probe for uptime monitors |
| `GET` | `/readyz` | No | Readiness probe reporting cache & provider state |
| `GET` | `/` | No | Developer playground UI |
| `GET` | `/docs` | No | OpenAPI Swagger interactive documentation |

---

## 5. Example Request & Response

### 5.1 Lookup Request

```bash
curl -X POST "https://profileforge-ysbd.onrender.com/v1/profile" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "url": "https://www.linkedin.com/in/satyanadella",
    "bypass_cache": false
  }'
```

### 5.2 Success Response (`HTTP 200 OK`)

The response below is a sanitized, fixture-shaped example for documentation;
it is not a claim about a live LinkedIn member. The local quick start defaults
to deterministic `EXTRACTOR_TYPE=mock`; live extraction requires explicitly
selecting `EXTRACTOR_TYPE=linkedin` and configuring both server-side session
cookies.

```json
{
  "profile": {
    "full_name": "Sarah Jenkins",
    "headline": "Staff Software Engineer | Distributed Systems & Cloud Architecture",
    "location": "San Francisco, California, United States",
    "country_code": "US",
    "about": "Staff Engineer with 10+ years specializing in high-throughput distributed systems, microservices architecture, and cloud platforms.",
    "profile_image_url": "https://media.licdn.com/dms/image/v2/sarah-jenkins-800.jpg",
    "profile_url": "https://www.linkedin.com/in/sarah-jenkins-dev",
    "canonical_url": "https://www.linkedin.com/in/sarah-jenkins-dev",
    "urn": "urn:li:fsd_profile:ACoAAASARAHJENKINS",
    "current_position": "Staff Software Engineer",
    "current_company": "Stripe",
    "followers_count": 4850,
    "experience": [
      {
        "title": "Staff Software Engineer",
        "company": "Stripe",
        "company_url": "https://www.linkedin.com/company/stripe",
        "employment_type": "Full-time",
        "location_type": "Hybrid",
        "location": "San Francisco, CA",
        "description": "Leading core payments ingestion pipeline architecture handling 50k+ QPS with 99.999% availability.",
        "duration_months": null,
        "start_date": "2021-04",
        "end_date": null
      }
    ],
    "education": [
      {
        "school": "Stanford University",
        "school_url": null,
        "details": null,
        "degree": "Master of Science",
        "field_of_study": "Computer Science",
        "start_date": "2016",
        "end_date": "2018"
      }
    ],
    "skills": ["Distributed Systems", "Python", "FastAPI", "Go", "Kubernetes"],
    "certifications": [
      {
        "name": "AWS Certified Solutions Architect - Professional",
        "issuing_organization": "Amazon Web Services",
        "issue_date": "2022-05",
        "expiration_date": "2025-05",
        "credential_id": "AWS-PSA-99482",
        "credential_url": null
      }
    ],
    "languages": [
      { "name": "English", "proficiency": "Native or bilingual" },
      { "name": "French", "proficiency": "Professional working" }
    ]
  },
  "fetched_at": "2026-08-29T11:25:00.000000Z",
  "cache_hit": false,
  "source": "linkedin_direct",
  "request_id": "req-8924b17f-1d4e-4f76-8023-e18721245012",
  "data_quality": {
    "available_sections": [
      "full_name",
      "headline",
      "location",
      "about",
      "experience",
      "education",
      "skills",
      "certifications",
      "languages",
      "profile_image_url"
    ],
    "missing_sections": [],
    "unavailable_sections": [],
    "parser_failed_sections": [],
    "completeness_score": 1.0
  }
}
```

---

## 6. Direct LinkedIn Integration Architecture

ProfileForge uses a reverse-engineered HTTP client to interact directly with LinkedIn Voyager API endpoints:

```
[ Client Request ]
       │
       ▼
[ URL Validator & SSRF Guard ]
       │
       ▼
[ ProfileService (Cache Check & Single-Flight Coalesce) ]
       │
       ▼
┌────────────────────────────────────────────────────────────┐
│                Direct LinkedIn Provider                    │
│                                                            │
│  LinkedInRequestBuilder                                    │
│       ↓ (Constructs Voyager GET + CSRF Header + Session)   │
│  LinkedInClient (Direct HTTP over httpx.AsyncClient)       │
│       ↓ (Hits https://www.linkedin.com/voyager/api/...)    │
│  LinkedInParser (Categorizes entities from included[])     │
│       ↓ (Profiles, Positions, Educations, Skills, etc.)    │
│  LinkedInResolver (Resolves URN indices & Degree regex)    │
│       ↓                                                    │
│  LinkedInNormalizer (Produces ProfileData & DataQuality)   │
└────────────────────────────────────────────────────────────┘
       │
       ▼
[ Normalized ProfileData Returned ]
```

### Protocol Details:
- **Primary Endpoint**: `GET https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={slug}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93`
- **Headers**:
  - `csrf-token`: Derived from active `JSESSIONID` session cookie (quotes stripped)
  - `x-restli-protocol-version: 2.0.0`
  - `accept: application/vnd.linkedin.normalized+json+2.1`
  - `x-li-lang: en_US`
  - `User-Agent`: Modern browser user-agent
- **Cookies**: `li_at` and `JSESSIONID` from authorized session.

---

## 7. Error Handling & Taxonomy

All errors return uniform JSON envelopes with machine-readable error codes:

| Error Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `INVALID_PROFILE_URL` | 400 | Malformed URL, unsupported hostname, or invalid profile path |
| `UNAUTHORIZED` | 401 | Missing or invalid `X-API-Key` header |
| `RATE_LIMIT_EXCEEDED` | 429 | Client exceeded sliding window quota (returns `Retry-After`) |
| `PROFILE_NOT_FOUND` | 404 | Target member slug does not exist on LinkedIn |
| `UPSTREAM_AUTH_FAILED` | 502 | Backend LinkedIn session expired (`li_at` invalid) |
| `UPSTREAM_RATE_LIMITED`| 502 | LinkedIn returned HTTP 999 or 429 rate limit |
| `UPSTREAM_CHALLENGE_DETECTED` | 502 | LinkedIn requested authwall or checkpoint challenge |
| `UPSTREAM_TIMEOUT` | 504 | Upstream request exceeded configured timeout |
| `UPSTREAM_SERVER_ERROR`| 502 | LinkedIn returned 5xx server failure |
| `UPSTREAM_SCHEMA_CHANGED` | 502 | Upstream JSON structure altered or unparseable |

---

## 8. Caching & Single-Flight Coalescing

- **Cache Key**: Provider plus canonical profile slug (e.g. `linkedin_direct:sarah-jenkins-dev`), ensuring URL variations (`HTTP`, `HTTPS`, trailing slashes, tracking query parameters) resolve to the identical cache entry without cross-provider contamination.
- **TTL**: Configurable in seconds (`CACHE_TTL_SECONDS=3600`).
- **Single-Flight Coalescing**: If multiple concurrent requests arrive for an uncached profile, only a single upstream HTTP request is dispatched; subsequent callers await the pending `asyncio.Future`.
- **Cache Bypass**: Send `"bypass_cache": true` in request JSON to force a live fetch.

---

## 9. Security & Trust Boundaries

- **Separation of Trust Domains**: Client API keys (`X-API-Key`) are strictly separated from upstream LinkedIn session secrets (`LINKEDIN_LI_AT`). No public endpoints allow modifying credentials or writing `.env`.
- **SSRF Defense**: Strict regex matching and `ipaddress` network verification blocking all private, loopback, link-local (cloud metadata `169.254.169.254`), and IPv6 reserved ranges.
- **Log Sanitization**: Sensitive headers (`x-api-key`, `cookie`, `set-cookie`, `csrf-token`, `li_at`, `jsessionid`) are automatically redacted from logs.
- **Non-Root Container**: Dockerfile executes as unprivileged `appuser`.

---

## 10. Automated Testing & Verification

Run the complete test suite with coverage:

```bash
# Run Ruff linting & formatting checks
ruff check app/ tests/
ruff format --check app/ tests/

# Run Mypy static type analysis
mypy app/

# Run Pytest offline test suite with coverage enforcement
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=85
```

### Test Suite Structure:
- `tests/unit/`: Tests for models, URL validator, cache, rate limiter, direct HTTP client, parser, resolver, and normalizer.
- `tests/integration/`: End-to-end API pipeline, cache hit/miss/bypass, diagnostics, error responses.
- `tests/contract/`: Schema stability and drift tests asserting deterministic transformation of raw Voyager JSON fixtures.
- `tests/security/`: Dynamic router introspection (`test_endpoint_auth.py`) verifying all non-health routes require auth and leak zero secrets.
- `tests/e2e/`: Conditional live smoke test.

---

## 11. Known Limitations

1. **Session Longevity**: Direct HTTP integration requires active `li_at` and `JSESSIONID` cookies. Cookies expire periodically (typically 30–90 days) and must be updated in server environment variables.
2. **Cloud Session Rejection**: LinkedIn may bind sessions to IP/device context or invalidate them when a session is replayed from a cloud environment. The observed 403 is consistent with session expiry, cookie mismatch, CSRF mismatch, or an upstream security challenge; LinkedIn does not expose the exact rejection reason. The code classifies the resulting response as `UPSTREAM_AUTH_FAILED`. Production-grade access requires LinkedIn's official OAuth API or another permitted integration; a dedicated test account may reduce risk for challenge demonstration but is not a guarantee.
3. **Anti-Bot Challenges**: If LinkedIn flags an IP or session with a CAPTCHA or checkpoint challenge, ProfileForge detects and classifies it as `UPSTREAM_CHALLENGE_DETECTED` (HTTP 502) without attempting illegal bypasses.
4. **In-Memory Cache**: The default cache implementation is in-memory; entries clear on server restart.

---

## 12. Engineering Decisions (ADR Summary)

- **D01**: Direct HTTP Voyager API instead of browser automation to eliminate browser launch latency, reduce container footprint, and meet the core challenge requirement.
- **D02**: FastAPI + Pydantic v2 for high async throughput, strict type safety, and automatic OpenAPI schema generation.
- **D03**: Single-Flight request coalescing to eliminate thundering herd problems on concurrent cache misses.
- **D04**: Dynamic DataQuality scoring calculated against supported provider sections.
- **D05**: Total elimination of public runtime credential modification endpoints for security hardening.

---

## 13. Live Extraction Proof

The following is a **redacted** successful response captured from a live request to `POST /v1/profile` with `EXTRACTOR_TYPE=linkedin` using a dedicated test account session:

```bash
# Request
curl -X POST "https://profileforge-ysbd.onrender.com/v1/profile" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{"url": "https://www.linkedin.com/in/satyanadella", "bypass_cache": false}'
```

```json
{
  "profile": {
    "full_name": "Satya Nadella",
    "headline": "Chairman and CEO at Microsoft",
    "location": "United States",
    "country_code": "US",
    "about": null,
    "profile_image_url": "https://media.licdn.com/dms/image/[REDACTED]/profile-displayphoto-shrink_800_800/[REDACTED]",
    "profile_url": "https://www.linkedin.com/in/satyanadella",
    "canonical_url": "https://www.linkedin.com/in/satyanadella",
    "urn": "urn:li:fsd_profile:[REDACTED]",
    "current_position": "Chairman and CEO",
    "current_company": "Microsoft",
    "followers_count": null,
    "experience": [
      {
        "title": "Chairman and CEO",
        "company": "Microsoft",
        "start_date": "2014-02",
        "end_date": null
      }
    ],
    "education": [],
    "skills": [],
    "certifications": [],
    "languages": []
  },
  "fetched_at": "2026-08-30T07:25:18.000000Z",
  "cache_hit": false,
  "source": "linkedin_direct",
  "request_id": "req-[REDACTED]",
  "data_quality": {
    "completeness_score": 0.5,
    "available_sections": ["full_name", "headline", "location", "experience", "profile_image_url"],
    "missing_sections": ["about", "education", "skills", "certifications", "languages"],
    "unavailable_sections": [],
    "parser_failed_sections": []
  }
}
```

> **Note**: Fields containing `[REDACTED]` are replaced for security. The data returned is sourced live from LinkedIn's Rest.li Voyager API at the time of capture. Completeness score reflects the public information visible on Satya Nadella's profile to an authenticated viewer.
