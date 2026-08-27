# ProfileForge — Extraction & Integration Research

## 1. Executive Summary

This document summarizes the reverse-engineering and integration research conducted for the ProfileForge Profile Lookup API.

### 1.1 Evaluated Provider Approaches
1. **Official LinkedIn API**: Restricted to enterprise partner scopes (Talent Solutions / Marketing). Does not support arbitrary public profile lookups for independent developers.
2. **Voyager API with `li_at` Session Cookie**: High ban risk, violates LinkedIn Terms of Service, blocked by anti-scraping fingerprinting (Spectroscopy). Rejected.
3. **Third-Party Legacy Proxies (e.g. Proxycurl)**: Defunct / shut down post-2025 litigation.
4. **LinkedAPI REST Workflow API**: Account-based automation using cloud-browser simulation on behalf of the developer's authorized LinkedIn account. **Selected**.

---

## 2. LinkedAPI REST Interface & Lifecycle

LinkedAPI provides a dedicated REST HTTP interface at `https://api.linkedapi.io`. All actions run as asynchronous **Workflows** to simulate human interaction rates.

### 2.1 Authentication Headers
Every request to `api.linkedapi.io` requires two credentials:
- `linked-api-token`: Developer account authorization token.
- `identification-token`: Identifier corresponding to the connected LinkedIn session.

### 2.2 Workflow Execution Protocol
```text
POST https://api.linkedapi.io/workflows
      ↓
Returns { workflowId, workflowStatus: "pending" | "running" }
      ↓
Loop GET https://api.linkedapi.io/workflows/{workflowId} every 3s
      ↓
Terminal Status: "completed" (with completion.data) OR "failed" (with failure.reason)
```

### 2.3 Verified Action Names & Expected Return Shapes
- `st.openPersonPage` (with `basicInfo: true`): Returns name, headline, location, countryCode, position, companyName, urn, followersCount.
- `st.retrievePersonExperience`: Returns structured list of experience entries with duration, startTime, endTime, company, title, description.
- `st.retrievePersonEducation`: Returns list of education records with schoolName, details.
- `st.retrievePersonSkills`: Returns skills list.
- `st.retrievePersonLanguages`: Returns languages list.

### 2.4 Unverified / Provisional Fields Status
- **Certifications**: Current documented finding: Not exposed in the primary `st.retrieve*` action set. Final status: Will be verified during live test request.
- **About / Summary**: Current documented finding: Not explicitly listed in basicInfo payload. Final status: Will check if returned in full profile object during live verification.
- **Profile Image**: Current documented finding: Not listed in documented sample. Final status: Will check if `profilePicture` or `avatar` key exists in live response.

---

## 3. Technology & Architecture Selections

### 3.1 Python Runtime Target: Python 3.12
- **Rationale**: Python 3.12 provides optimal production stability, mature binary wheels for all dependencies (`pydantic-core`, `uvicorn`, `httpx`), and predictable async event loop performance.
- **Verification**: All core dependencies (`fastapi`, `pydantic>=2.0`, `httpx>=0.27`, `structlog`, `pytest`, `pytest-asyncio`) have first-class support on Python 3.12.

### 3.2 Production Docker Base: `python:3.12-slim`
- Because we communicate with LinkedAPI via HTTP REST rather than running local browser subprocesses or Node.js CLI packages, **Node.js is completely excluded from the production image**.
- Produces a minimal, secure container image (~130MB) with a non-root execution user.

### 3.3 Concurrency & Protection Strategy
- **Application Semaphore**: `MAX_CONCURRENT_EXTRACTIONS=2` (configurable) to prevent downstream request bursts from overloading the single-seat LinkedAPI queue.
- **Sliding Window Rate Limiter**: Per-API-key rate limiting (e.g. 60 req/min) implemented in middleware.
- **Cache**: In-memory cache keyed by canonical LinkedIn profile identifier (e.g. `williamhgates`) with configurable TTL (default: 3600s).

---

## 4. Multi-Layered Secret Audit Protocol

To maintain zero secret leakage across the codebase, tests, and documentation:
1. **Automated Secret Scanner**: Regex scan across all files excluding `.git` for token patterns, cookies, and keys.
2. **Git Tracking Audit**: `git ls-files` to ensure no `.env`, credentials, or temporary debug logs are staged.
3. **Fixture Sanitization**: All fixtures under `tests/fixtures/raw_upstream/` are inspected to verify synthetic names, zero authentication tokens, and scrubbed identifiers.
4. **Log Redaction**: Structured logger middleware explicitly redacts `linked-api-token`, `identification-token`, `x-api-key`, and `authorization` headers.
