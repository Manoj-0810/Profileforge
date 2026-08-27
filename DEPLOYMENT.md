# ProfileForge — Deployment & Infrastructure Guide

## 1. Overview

ProfileForge is packaged as a standard container running on `python:3.12-slim` listening on `PORT=10000`. It is designed for seamless deployment on **Render.com** (Web Service Docker environment) or any modern container orchestration platform.

---

## 2. Deploying to Render.com

### 2.1 One-Click Blueprint Deployment (`render.yaml`)
The repository includes a `render.yaml` blueprint defining the service topology:

1. Log into your [Render.com Dashboard](https://dashboard.render.com).
2. Click **Blueprints** $\rightarrow$ **New Blueprint Instance**.
3. Select your connected `profileforge` repository.
4. Render automatically parses `render.yaml` and initializes the web service.

### 2.2 Manual Web Service Configuration
Alternatively, create a Web Service manually:
- **Environment**: `Docker`
- **Region**: `Oregon (US West)` or `Frankfurt (EU Central)`
- **Branch**: `main` or `master`
- **Dockerfile Path**: `./Dockerfile`
- **Health Check Path**: `/healthz`

### 2.3 Required Environment Variables

Configure these secrets in the Render Dashboard (**Environment** tab):

| Variable Name | Required | Recommended Value / Notes |
| :--- | :--- | :--- |
| `PORT` | Yes | `10000` |
| `ENVIRONMENT` | Yes | `production` |
| `EXTRACTOR_TYPE` | Yes | `linkedapi` (or `mock` for dry run) |
| `API_KEYS` | Yes | Comma-separated client keys (e.g. `prod-api-key-9a8f21`) |
| `LINKEDAPI_TOKEN` | If `linkedapi` | LinkedAPI Developer token from app.linkedapi.io |
| `LINKEDAPI_IDENTIFICATION_TOKEN` | If `linkedapi` | LinkedIn session token from app.linkedapi.io |
| `MAX_CONCURRENT_EXTRACTIONS` | No | `2` |
| `CACHE_TTL_SECONDS` | No | `3600` |
| `UPSTREAM_TIMEOUT_SECONDS` | No | `120.0` |

---

## 3. Local Development & Container Execution

### 3.1 Running with Docker Compose
```bash
# Set environment variables in .env (copy from .env.example)
cp .env.example .env

# Build and launch service
docker compose up --build -d

# Check service logs
docker compose logs -f
```

### 3.2 Running Directly with Python
```bash
# Install dependencies
pip install -r requirements.txt

# Start Uvicorn ASGI server
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

---

## 4. Verifying Public HTTPS Deployment

Once deployed on Render, verify liveness and profile lookup:

```bash
# 1. Health Check
curl -i https://YOUR_SERVICE_NAME.onrender.com/healthz

# 2. Readiness Check
curl -i https://YOUR_SERVICE_NAME.onrender.com/readyz

# 3. Profile Lookup
curl -X POST https://YOUR_SERVICE_NAME.onrender.com/v1/profile \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_CONFIGURED_API_KEY" \
  -d '{"url": "https://www.linkedin.com/in/sarah-jenkins-dev"}'
```
