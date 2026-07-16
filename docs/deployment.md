# Deployment

## Packaging

| Artifact | File | Purpose |
|----------|------|---------|
| Compose stack | `docker-compose.yml` | Local multi-service (Postgres + API + Vite) |
| API image | `backend/Dockerfile` | Targets: `production` (default for Compose backend), `development` (tests) |
| UI image | `frontend/Dockerfile` | Targets: `production` (nginx SPA), `development` (Vite), `build` |
| CI | `.github/workflows/ci.yml` | Ruff, mypy, pytest, frontend typecheck/build, Docker builds |

Backend entrypoint:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend production image serves `dist/` via nginx (`frontend/nginx.conf`) with baseline security headers/CSP.

## Local production image check

```bash
docker compose up --build -d
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/live
curl -sS http://localhost:8000/ready
docker build --target production -t signalflow-frontend:prod ./frontend
```

## Production configuration

Fail-fast when `SIGNALFLOW_ENVIRONMENT=production|prod`:

- `JWT_SECRET`
- `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY`
- `SIGNALFLOW_FRONTEND_ORIGIN` (non-localhost)
- `AUTH_COOKIE_SECURE=true`
- Live mode: Retell signature material; Cal.com webhook secret when Cal.com key present

Also set:

- Managed `SIGNALFLOW_DATABASE_URL`
- `APP_PUBLIC_API_URL` for webhook registration
- `LOG_JSON=true`, `LOG_LEVEL=INFO`
- `RATE_LIMIT_ENABLED=true`
- Keep `ALLOW_LIVE_BOOKING=false` until final acceptance

## Platform guides

### Render

1. Create **PostgreSQL** instance; copy internal URL into `SIGNALFLOW_DATABASE_URL` (psycopg form: `postgresql+psycopg://…`).
2. **Web service** from repo: Dockerfile path `backend/Dockerfile`, Docker context `backend`.
3. Set env vars (secrets in Render dashboard). Health check path: `/ready`.
4. Static site or second service for frontend: build `frontend` with `VITE_API_URL=https://api.example.com`, or deploy nginx production image.
5. Point custom domains + TLS; set `SIGNALFLOW_FRONTEND_ORIGIN` to the dashboard origin.

### Railway

1. Add Postgres plugin.
2. Deploy backend service from `backend/` Dockerfile; inject env from Railway variables.
3. Healthcheck `/ready`.
4. Deploy frontend as static or Docker `production` target with build arg `VITE_API_URL`.
5. Enable public HTTPS domains; update CORS origin and webhook URLs.

### DigitalOcean App Platform

1. Create app with Dockerfile component for backend (`backend/Dockerfile`).
2. Attach Managed Database (Postgres 16).
3. Configure env / secrets; HTTP health check `/ready`.
4. Static site component for frontend build, or container with nginx production stage.
5. Spaces optional for future media; not required for MVP.

### AWS (recommended shape)

1. **RDS PostgreSQL 16** with automated backups + Multi-AZ for first paying customer.
2. **ECS Fargate** (or App Runner) running backend production image; ALB health checks on `/ready`.
3. **Secrets Manager** / SSM for `JWT_SECRET`, encryption key, provider keys.
4. **CloudFront + S3** (or Amplify) for frontend `npm run build` artifacts.
5. **WAF** rate rules in front of `/api/auth` and `/api/webhooks` (complements in-app limiter).
6. **CloudWatch** scrape or sidecar for `/metrics`; alarms on 5xx and unhealthy targets.
7. Optional: Route 53 + ACM certificates.

## Migrations

Prefer a dedicated migrate step in CD before shifting traffic. Compose uses upgrade-on-start for local/dev.

## Rollback

1. Redeploy previous application image.
2. If schema changed: restore from backup or carefully `alembic downgrade` after verifying data safety ([operations.md](operations.md)).
3. Confirm `/ready` and auth cookie login.

## CI builds

GitHub Actions on `main` PRs/pushes: backend quality, frontend typecheck/build, Docker backend + frontend production/development images.

See [production-readiness.md](production-readiness.md), [operations.md](operations.md), [monitoring.md](monitoring.md).
