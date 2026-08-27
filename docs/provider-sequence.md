# LinkedAPI Workflow Lifecycle, Retry Policy & Request Coalescing

## 1. Overview

This document details:
1. The asynchronous workflow execution sequence.
2. The deterministic **Retry & Backoff Policy** across transient vs terminal failure states.
3. The **Single-Flight Duplicate Request Protection** (request coalescing) mechanism.

---

## 2. Sequence Diagram with Request Coalescing

```mermaid
sequenceDiagram
    autonumber
    participant C1 as Client 1 (Request for "williamhgates")
    participant C2 as Client 2 (Request for "williamhgates")
    participant API as FastAPI Router
    participant Svc as ProfileService (SingleFlight)
    participant Cache as InMemoryCache
    participant Sem as Concurrency Semaphore
    participant Adapter as LinkedAPI Provider Adapter
    participant Remote as api.linkedapi.io

    C1->>API: POST /v1/profile { "url": ".../williamhgates" }
    C2->>API: POST /v1/profile { "url": ".../williamhgates" }
    API->>Svc: lookup("williamhgates") (C1)
    API->>Svc: lookup("williamhgates") (C2)
    
    Svc->>Cache: get("williamhgates") -> MISS
    Note over Svc: C1 registers in-flight Future for "williamhgates"
    Note over Svc: C2 detects existing in-flight Future and attaches (awaits same Future)
    
    Svc->>Sem: acquire() (C1 only)
    Sem->>Adapter: fetch("williamhgates")
    
    Adapter->>Remote: POST /workflows
    Remote-->>Adapter: { workflowId: "wf-123", workflowStatus: "pending" }
    
    loop Polling (every 3s with deadline)
        Adapter->>Remote: GET /workflows/wf-123
        Remote-->>Adapter: { workflowStatus: "running" / "completed" }
    end
    
    Adapter->>Adapter: Parse -> Resolve -> Normalize
    Adapter-->>Sem: ProfileData
    Sem-->>Svc: ProfileData
    
    Note over Svc: Svc stores in Cache("williamhgates")
    Note over Svc: Svc resolves in-flight Future with ProfileData
    
    Svc-->>API: ProfileLookupResponse (for C1)
    Svc-->>API: ProfileLookupResponse (for C2, cache_hit=True/coalesced)
    API-->>C1: HTTP 200 JSON Response
    API-->>C2: HTTP 200 JSON Response
```

---

## 3. Explicit Retry & Backoff Policy

Not all errors are equal. Retrying non-transient errors (like invalid authentication or explicit rate limits) exacerbates upstream penalties and degrades reliability.

### 3.1 Classification Matrix

| Failure Category | HTTP Codes / Errors | Retryable? | Max Attempts | Backoff Strategy | Resulting App ErrorCode |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Transient Network / DNS** | `ConnectTimeout`, `ReadTimeout`, `ConnectError` | **Yes** | 3 | Exponential with jitter ($2^n \times 0.5s \pm 0.1s$) | `UPSTREAM_TIMEOUT` / `UPSTREAM_SERVER_ERROR` |
| **Upstream Transient 5xx** | `HTTP 502`, `HTTP 503`, `HTTP 504` | **Yes** | 2 | Exponential ($1s, 2s$) | `UPSTREAM_SERVER_ERROR` |
| **Authentication & Config** | `invalidLinkedApiToken`, `subscriptionRequired`, `401`, `403` | **No** | 1 (Fail fast) | None | `AUTH_CONFIGURATION_ERROR` |
| **Rate Limit Exceeded** | `tooManyRequests`, `limitExceeded`, `429` | **No** | 1 (Fail fast) | Respect `Retry-After` if present | `UPSTREAM_RATE_LIMITED` |
| **Terminal Account State** | `linkedinAccountSignedOut`, `outsideWorkingHours` | **No** | 1 (Fail fast) | None | `UPSTREAM_AUTH_FAILED` / `UPSTREAM_CHALLENGE_DETECTED` |
| **Target Profile Missing** | `personNotFound`, `404` | **No** | 1 (Fail fast) | None | `PROFILE_NOT_FOUND` |
| **Schema Validation Drift** | Parser validation exception | **No** | 1 (Fail fast) | None | `UPSTREAM_SCHEMA_CHANGED` |

---

## 4. Single-Flight Duplicate Request Protection

To prevent "cache stampedes" or redundant slow extractions when multiple consumers query the same profile simultaneously:
1. `ProfileService` maintains an internal dictionary `_in_flight: dict[str, asyncio.Future[ProfileData]]`.
2. When a request for canonical profile ID $K$ arrives:
   - If $K$ is in `_in_flight`, the caller simply awaits the existing future.
   - If $K$ is not in `_in_flight`, a new Future is registered, the single upstream extraction workflow executes, populates the cache, resolves the future for all waiters, and removes $K$ from `_in_flight` in a `finally` block.
3. If an extraction fails, the exception propagates to all concurrent waiters cleanly.
