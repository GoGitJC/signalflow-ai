# Render backend deployment

Production API for SignalFlow AI runs on **Render** as a Docker web service with **Render Managed PostgreSQL**.

> **Do not deploy until a human approves.** This document is configuration-only.

## Architecture role

```text
api.<DOMAIN>  →  Cloudflare  →  Render Web Service (FastAPI)
                                      │
                                      └─ Render PostgreSQL 16
```

## Prerequisites

- Render account
- GitHub repo connected to Render
- Domain ready in Cloudflare (see [cloudflare.md](cloudflare.md))
- Secrets prepared from [`.env.production.example`](../../.env.production.example)

## Blueprint (`render.yaml`)

Repository root includes [`render.yaml`](../../render.yaml):

| Resource | Name | Notes |
|----------|------|-------|
| PostgreSQL 16 | `signalflow-db` | Managed; enable backups in dashboard |
| Web service | `signalflow-api` | Docker from `backend/`, health `/ready` |

### Apply blueprint

1. Render Dashboard → **New** → **Blueprint**
2. Select the GitHub repository and branch (merge to `main` first, or deploy from approved branch)
3. Review `render.yaml`
4. Fill all `sync: false` secrets in the UI
5. Set public URLs:
   - `APP_PUBLIC_API_URL=https://api.<DOMAIN>`
   - `CORS_ORIGINS=https://www.<DOMAIN>,https://app.<DOMAIN>`
   - `SIGNALFLOW_FRONTEND_ORIGIN=https://www.<DOMAIN>`
   - `TRUSTED_HOSTS=api.<DOMAIN>,*.onrender.com`

### Manual service (alternative)

1. **New PostgreSQL** → note Internal Database URL
2. **New Web Service** → Docker
   - Root directory: `backend`
   - Dockerfile path: `./Dockerfile`
   - Docker context: `.`
3. Health check path: `/ready`
4. Auto-deploy: enabled on `main`

## Docker production image

`backend/Dockerfile` final stage `production`:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Render sets `PORT`; the image listens on `8000` by default. If Render requires `$PORT`, either:

- Keep Render Docker port mapping to 8000, or
- Override start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Database URL

Render provides `postgresql://…`. Settings auto-normalize to `postgresql+psycopg://…`.

Prefer the **Internal** Database URL for the web service (lower latency, no egress).

## Migrations

Run automatically on container start (`alembic upgrade head`).

For a safer CD pattern later: run migrations as a one-off job before traffic shift. Until then, ensure only one instance starts during schema changes or use Render’s zero-downtime carefully.

Rollback: see [disaster-recovery.md](disaster-recovery.md).

## Health checks

| Path | Use on Render |
|------|----------------|
| `/ready` | **Health check path** (DB must respond) |
| `/live` | Process up (optional secondary) |
| `/health` | Alias of liveness |
| `/metrics` | Scrape from private network / allowlisted IP |

## Custom domain

1. Render service → **Settings** → **Custom Domains** → `api.<DOMAIN>`
2. Add Cloudflare CNAME `api` → Render hostname (see [cloudflare.md](cloudflare.md))
3. Wait for TLS certificate issued by Render (or Cloudflare Full Strict)

## Automatic deploys

With `autoDeploy: true`, pushes to the connected branch redeploy the API. Protect `main` with required CI checks.

## Post-deploy smoke

```bash
curl -fsS https://api.<DOMAIN>/live
curl -fsS https://api.<DOMAIN>/ready
curl -fsS https://api.<DOMAIN>/health
curl -fsS https://api.<DOMAIN>/metrics | head
```

Confirm CORS preflight from the dashboard origin and cookie login (`AUTH_COOKIE_SECURE=true`).
