# Phase 3C – Dashboard MVP Staging Deployment Guide

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Browser                                        │
│  ┌─────────────────────────────────────────┐    │
│  │  Next.js Dashboard (apps/dashboard)     │    │
│  │  Port 3000                              │    │
│  └──────────────┬──────────────────────────┘    │
│                 │ API calls (x-api-key header)  │
│  ┌──────────────▼──────────────────────────┐    │
│  │  FastAPI Backend (backend/)             │    │
│  │  Port 8000                              │    │
│  │  CORS: allows FRONTEND_URL origins      │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Local Development

### 1. Seed the database (first time only)

```bash
cd backend
.\venv\Scripts\activate
python scripts/seed_dashboard_key.py
```

This creates:
- Tenant: `tenant-dashboard-dev`
- API key: `test_api_key` with `admin` scope

### 2. Start the backend

```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 3. Start the dashboard

```bash
cd apps/dashboard
npm install    # first time only
npm run dev
```

- Dashboard: http://localhost:3000
- Backend: http://localhost:8000

### 4. API Key configuration

The dashboard resolves the API key in this order:
1. **localStorage** — if a key was stored via browser (manual override)
2. **`NEXT_PUBLIC_API_TOKEN`** — env var in `.env.local` (default: `test_api_key`)

For local dev, the env var default + seed script is sufficient.

---

## Staging Deployment

### Backend (Cloud Run)

The backend deploys via the existing `cloudbuild.yaml`. Required env vars:

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Cloud SQL connection string |
| `EVIDENCE_HMAC_SECRET` | Yes | HMAC signing key for evidence chain |
| `FRONTEND_URL` | Yes | Dashboard origin for CORS (e.g. `https://dashboard.example.com`). Comma-separated for multiple origins. |
| `STRIPE_API_KEY` | Yes | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |

### Dashboard (Vercel / Cloud Run)

#### Option A: Vercel

1. Connect the `apps/dashboard` directory to Vercel.
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://<backend-cloud-run-url>`
   - `NEXT_PUBLIC_API_TOKEN` = your staging API key
3. Deploy.

#### Option B: Cloud Run

The dashboard uses `output: 'standalone'` in `next.config.js` for optimized Docker builds.

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Deploy:
```bash
gcloud run deploy dashboard \
  --image gcr.io/PROJECT/dashboard \
  --set-env-vars NEXT_PUBLIC_API_URL=https://backend-url,NEXT_PUBLIC_API_TOKEN=staging_key \
  --port 3000 \
  --allow-unauthenticated
```

---

## CORS Configuration

The backend reads `FRONTEND_URL` from config and uses it as the CORS `allow_origins` list.
- Default: `http://localhost:3000`
- Supports comma-separated origins: `https://dash.example.com,http://localhost:3000`
- Credentials are allowed (cookies, auth headers).

---

## Environment Variables Reference

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Dashboard | `http://localhost:8000` | Backend API base URL |
| `NEXT_PUBLIC_API_TOKEN` | Dashboard | `test_api_key` | Fallback API key for auth |
| `FRONTEND_URL` | Backend | `http://localhost:3000` | CORS allowed origins |
| `STRIPE_API_KEY` | Backend | — | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Backend | — | Stripe webhook signing secret |

---

## Pages Available

| Route | Description |
|---|---|
| `/systems` | List and navigate AI systems |
| `/systems/:id` | System detail with linked features |
| `/features` | List registered features |
| `/features/:id` | Feature detail with versions |
| `/reviews` | Review tasks with status filtering |
| `/evidence` | Evidence logs with risk/decision filters |
| `/billing` | Subscription, entitlements, checkout |
| `/runtime` | Governed request playground |

---

## Backend Changes for Phase 3C

Two minimal backend changes were made:

1. **CORS Middleware** — Added `CORSMiddleware` to `app/main.py` using `FRONTEND_URL`
   from config as the allowed origin list. No wildcard in staging/production.

2. **Seed Script** — Added `scripts/seed_dashboard_key.py` to create a dev tenant
   and API key for local dashboard testing.

No new endpoints, models, or services were added.
