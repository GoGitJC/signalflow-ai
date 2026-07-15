# Troubleshooting

## `DuplicateObject: type "userrole" already exists`

Cause: Alembic enum created twice (explicit create + table DDL). Fixed in `0001_initial` via `postgresql.ENUM(..., create_type=False)`.

Recovery on a broken volume:

```bash
docker compose down -v
docker compose up --build
```

## Backend exits immediately after start

```bash
docker compose logs backend --tail 100
```

Common causes: migration failure, bad `SIGNALFLOW_DATABASE_URL`, DB not healthy yet.

## Health check fails

```bash
curl -v http://localhost:8000/health
docker compose ps
```

Ensure `backend` is `Up` and port `8000` is free on the host.

## Dashboard empty / wrong tenant

Confirm `VITE_BUSINESS_ID` matches a real business UUID and recreate frontend:

```bash
docker compose up -d --force-recreate frontend
```

Also check `localStorage.signalflow_business_id`.

## Webhook 401

Signature verification failed. Clear secrets for local unsigned simulation, or compute a valid HMAC with the configured secret.

## Integration routes return 501

`SIGNALFLOW_MOCK_EXTERNAL_SERVICES=false` without live clients. Set back to `true` for local mock flows.

## Frontend build / `tsc` errors

```bash
cd frontend && npm ci && npx tsc --noEmit && npm run build
```

Ensure Node 20+.

## Port already in use

Stop other Postgres/API processes or change Compose host ports.
