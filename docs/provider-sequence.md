# ProfileForge — Provider Execution Sequence

## 1. Direct Extraction Flow (Happy Path)

The following Mermaid sequence diagram illustrates the lifecycle of a profile lookup request through the direct LinkedIn HTTP architecture:

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant FastAPI as FastAPI (/v1/profile)
    participant Auth as Auth & Rate Limit
    participant URL as URL Validator
    participant Svc as ProfileService
    participant Cache as InMemoryCache
    participant Ext as DirectLinkedInExtractor
    participant Req as LinkedInRequestBuilder
    participant Http as LinkedInClient (HTTP)
    participant LI as LinkedIn Voyager API
    participant Parser as LinkedInParser
    participant Res as LinkedInResolver
    participant Norm as LinkedInNormalizer

    Client->>FastAPI: POST /v1/profile {url, bypass_cache}
    FastAPI->>Auth: Validate X-API-Key & Sliding Window Quota
    Auth-->>FastAPI: Key Validated
    FastAPI->>URL: Validate URL & Extract Slug
    URL-->>FastAPI: Canonical URL + Member Slug
    FastAPI->>Svc: lookup(canonical_url, slug)
    Svc->>Cache: get(provider + canonical slug)

    alt Cache HIT (bypass_cache == False)
        Cache-->>Svc: ProfileData
        Svc-->>FastAPI: ProfileLookupResponse (cache_hit=True)
    else Cache MISS or bypass_cache == True
        Svc->>Ext: fetch(canonical_url)
        Ext->>Req: build_profile_request(slug)
        Req-->>Ext: URL, Headers (csrf-token, RestLi), Cookies (li_at, JSESSIONID)
        Ext->>Http: execute_request(req)
        Http->>LI: GET /voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={slug}&decorationId=...
        LI-->>Http: 200 OK + Normalized JSON (data + included[])
        Http-->>Ext: Raw JSON Payload
        Ext->>Parser: parse(raw_json)
        Parser-->>Ext: ParsedEntities (Profile, Positions, Educations, Skills, etc.)
        Ext->>Res: resolve(parsed_entities)
        Res-->>Ext: ResolvedProfileGraph
        Ext->>Norm: normalize(resolved_graph, canonical_url)
        Norm-->>Ext: ProfileData + DataQuality
        Ext-->>Svc: ProfileData
        Svc->>Cache: set(provider + canonical slug, ProfileData, ttl)
        Svc-->>FastAPI: ProfileLookupResponse (cache_hit=False)
    end

    FastAPI-->>Client: 200 OK + JSON Payload + X-Request-ID
```

---

## 2. Upstream Error & Challenge Handling Flow

```mermaid
sequenceDiagram
    autonumber
    participant Ext as DirectLinkedInExtractor
    participant Http as LinkedInClient (HTTP)
    participant LI as LinkedIn Voyager API
    participant Svc as ProfileService

    Ext->>Http: execute_request(slug)
    Http->>LI: GET /voyager/api/identity/dash/profiles...

    alt 401 Unauthorized / Session Expired
        LI-->>Http: 401 Unauthorized
        Http-->>Ext: raise UpstreamAuthError
        Ext-->>Svc: ProfileForgeError(UPSTREAM_AUTH_FAILED, 502)
    else 404 Member Not Found
        LI-->>Http: 404 Not Found
        Http-->>Ext: raise ProfileNotFoundError
        Ext-->>Svc: ProfileForgeError(PROFILE_NOT_FOUND, 404)
    else 429 / HTTP 999 Bot Challenge
        LI-->>Http: 999 Request Denied / 429 Too Many Requests
        Http-->>Ext: raise UpstreamRateLimitError
        Ext-->>Svc: ProfileForgeError(UPSTREAM_RATE_LIMITED, 502)
    else 302 Redirect to /authwall or /checkpoint
        LI-->>Http: 302 Redirect to /authwall
        Http-->>Ext: raise UpstreamChallengeError
        Ext-->>Svc: ProfileForgeError(UPSTREAM_CHALLENGE_DETECTED, 502)
    else 500 / 502 / 503 Upstream Transient Error
        LI-->>Http: 503 Service Unavailable
        Note over Http: Retry with exponential backoff (up to 2 retries)
        Http->>LI: Retry attempt 1
        LI-->>Http: 503 Service Unavailable
        Http-->>Ext: raise UpstreamServerError
        Ext-->>Svc: ProfileForgeError(UPSTREAM_SERVER_ERROR, 502)
    end
```
