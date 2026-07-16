# Deployment

Production topology for SignalFlow AI:

```text
Internet
   │
Cloudflare DNS + TLS
   │
   ├─ www.<DOMAIN> / app.<DOMAIN>  →  Vercel (React SPA)
   │
   └─ api.<DOMAIN>                 →  Render (FastAPI Docker)
                                         │
                                         └─ Render Managed PostgreSQL 16
                                                │
                                         Retell · Cal.com · Twilio
```

> Cloud deploy is **manual and human-approved**. This repo ships configuration and docs only.

## Provider guides

| Guide | Path |
|-------|------|
| Render (API + DB) | [deployment/render.md](deployment/render.md) |
| Vercel (frontend) | [deployment/vercel.md](deployment/vercel.md) |
| Cloudflare (DNS/TLS) | [deployment/cloudflare.md](deployment/cloudflare.md) |
| Ordered checklist | [deployment/checklist.md](deployment/checklist.md) |
| Disaster recovery | [deployment/disaster-recovery.md](disaster-recovery.md) |
| Launch gate | [../LAUNCH_CHECKLIST.md](../LAUNCH_CHECKLIST.md) |

## Packaging (local / CI)

| Artifact | File | Purpose |
|----------|------|---------|
| Compose stack | `docker-compose.yml` | Local multi-service |
| API image | `backend/Dockerfile` | `production` / `development` |
| UI image | `frontend/Dockerfile` | nginx SPA / Vite / build |
| Render blueprint | `render.yaml` | API + Postgres |
| Vercel config | `frontend/vercel.json` | SPA rewrites + headers |
| Prod env template | `.env.production.example` | Secret checklist |

## Local verification

```bash
docker compose up --build -d
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/live
curl -fsS http://localhost:8000/ready
```

## Production configuration highlights

- `APP_ENV` / `SIGNALFLOW_ENVIRONMENT=production` — fail-fast validation
- `CORS_ORIGINS=https://www.<DOMAIN>,https://app.<DOMAIN>`
- `AUTH_COOKIE_SECURE=true`, `AUTH_COOKIE_SAMESITE=lax`
- `APP_PUBLIC_API_URL=https://api.<DOMAIN>`
- `VITE_API_URL=https://api.<DOMAIN>` (Vercel build-time)
- Keep `ALLOW_LIVE_BOOKING=false` until Final Acceptance

## Rollback summary

1. Vercel: promote previous deployment  
2. Render: rollback previous deploy  
3. Database: restore from backup / PITR — [disaster-recovery.md](deployment/disaster-recovery.md)

See also [production-readiness.md](production-readiness.md), [operations.md](operations.md), [monitoring.md](monitoring.md), [security.md](security.md).
