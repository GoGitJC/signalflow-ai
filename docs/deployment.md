# Deployment

## Current packaging

| Artifact | File | Purpose |
|----------|------|---------|
| Compose stack | `docker-compose.yml` | Local multi-service run |
| API image | `backend/Dockerfile` | `pip install .` + migrate + uvicorn |
| UI image | `frontend/Dockerfile` | `npm ci` + Vite **dev** server (local) |

Backend container entrypoint:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Recommended production shape

1. **Managed PostgreSQL** with automated backups and TLS to the app.
2. **API** on a container platform (Render, Railway, Fly.io, ECS, or DigitalOcean App Platform) using a production image that runs `uvicorn` (or gunicorn+uvicorn workers) behind HTTPS.
3. **Frontend** built with `npm run build` and served via CDN / static hosting (or nginx), with `VITE_API_URL` pointed at the public API.
4. **Secrets** injected by the platform — never bake `.env` into images.
5. **Webhook URLs** registered with Retell/Cal.com pointing at the public API.

## Environment (production)

- Set `SIGNALFLOW_ENVIRONMENT=production`
- Set `SIGNALFLOW_MOCK_EXTERNAL_SERVICES=false` only after live clients exist
- Configure `SIGNALFLOW_FRONTEND_ORIGIN` to the dashboard origin
- Provide webhook secrets and (when ready) Twilio credentials
- Provide `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` before storing provider credentials

## Migrations in production

Run Alembic as a release step before or at container start (Compose already does upgrade-on-start). Prefer a dedicated migrate job in CI/CD for larger environments.

## Rollback

1. Redeploy previous application image.
2. If schema changed, `alembic downgrade` to the prior revision only after verifying data safety.
3. Keep database backups prior to every migration.

## CI builds

GitHub Actions builds backend and frontend Docker images on pull requests (`.github/workflows/ci.yml`).

See also [production-readiness.md](production-readiness.md).
