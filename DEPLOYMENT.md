# ProfileForge — Deployment & Infrastructure Guide

## 1. Overview

ProfileForge is packaged as a lightweight container using `python:3.12-slim` running as an unprivileged user (`appuser`) on `PORT=10000`. It is designed for simple, reproducible deployment on **Render.com** (Web Service Docker environment) or any cloud container platform.

---

## 2. Deploying to Render.com

### 2.1 One-Click Blueprint Deployment (`render.yaml`)
The repository includes a `render.yaml` blueprint defining the service topology:

1. Log into your [Render.com Dashboard](https://dashboard.render.com).
2. Click **Blueprints** $\rightarrow$ **New Blueprint Instance**.
3. Select your connected `profileforge` repository.
4. Render automatically parses `render.yaml` and initializes the web service with HTTPS TLS termination.

### 2.2 Required Environment Variables

Configure these variables in the Render Dashboard (**Environment** tab):

| Variable Name | Required | Description |
| :--- | :--- | :--- |
| `PORT` | Yes | `10000` |
| `ENVIRONMENT` | Yes | `production` |
| `EXTRACTOR_TYPE` | Yes | `linkedin` (or `mock` for deterministic demo) |
| `API_KEYS` | Yes | Comma-separated client keys (e.g. `prod-secret-key-123`) |
| `LINKEDIN_LI_AT` | If `linkedin` | `li_at` cookie from an authorized LinkedIn session |
| `LINKEDIN_JSESSIONID` | If `linkedin` | `JSESSIONID` cookie from an authorized LinkedIn session |
| `LINKEDIN_USER_AGENT` | No | Realistic browser user-agent |
| `MAX_CONCURRENT_EXTRACTIONS` | No | `2` |
| `CACHE_TTL_SECONDS` | No | `3600` |
| `UPSTREAM_TIMEOUT_SECONDS` | No | `30.0` |
| `RATE_LIMIT_REQUESTS` | No | `60` |
| `RATE_LIMIT_WINDOW_SECONDS` | No | `60` |

---

## 3. Local Execution & Docker

### 3.1 Running with Docker

```bash
# 1. Build production image
docker build -t profileforge .

# 2. Run container
docker run -p 10000:10000 --env-file .env profileforge
```

### 3.2 Running Directly with Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 10000
```
