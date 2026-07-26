# Operations

Day-2 runbook for Verideum in production.

## Health probes

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `GET /live` | Process liveness | `200` `{ "status": "ok" }` |
| `GET /health` | Alias of liveness | `200` |
| `GET /ready` | DB reachability | `200` with `checks.database=ok`; `503` if DB down |
| `GET /metrics` | Prometheus text metrics | `200` plain text |

Configure platform health checks:

- **Liveness:** `/live` (or `/health`)
- **Readiness:** `/ready` (do not route traffic until ready)

## Logging

- Structured JSON logs when `LOG_JSON=true` (recommended in production; default true).
- Level via `LOG_LEVEL` (`INFO`, `WARNING`, `ERROR`, `DEBUG`).
- Every request gets `X-Request-ID` (echoed on responses and in error payloads as `error.request_id`).
- Do **not** log passwords, JWTs, API keys, full webhook bodies, or raw phone numbers. Redaction helpers live in `app.core.logging`.

## Rate limiting

In-memory fixed-window limits (per process) when `RATE_LIMIT_ENABLED=true`:

- `/api/auth/*` — login/register protection
- `/api/webhooks/*` and `/api/retell/*` — webhook/tool burst protection

For multi-instance production, front with a platform rate limiter (or Redis) later; the in-process limiter is a baseline.

## Backups (PostgreSQL)

### What to back up

- Full database dump (schema + data)
- Prefer continuous / PITR on managed Postgres (Render, RDS, DO Managed DB, etc.)

### Manual dump (example)

```bash
pg_dump "$DATABASE_URL" --format=custom --file="signalflow-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Store dumps encrypted off-host. Retain at least 7 daily + 4 weekly for first customers.

### Restore procedure

1. Stop writers (scale API to 0 or put maintenance page).
2. Provision empty database (or drop/recreate schema carefully).
3. Restore:

```bash
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" signalflow-YYYYMMDD.dump
```

4. Run `alembic upgrade head` if the dump is from an older revision and you need newer migrations.
5. Hit `/ready`, then `/health`, then smoke-test login + one dashboard list endpoint.
6. Re-enable traffic.

### Migration rollback

1. Take a fresh backup **before** every production migration.
2. Prefer forward-fix migrations. If rollback is required:

```bash
alembic downgrade -1   # or alembic downgrade <prior_revision>
```

3. Redeploy the application image that matches the schema revision.
4. Verify `/ready` and critical flows (auth cookies, calls list, webhook POST).

Never downgrade past a revision that deleted irreversible data without a restore from backup.

## Demo data

```bash
docker compose run --rm backend python -m app.cli.seed_demo
# optional: --reset
```

Credentials and contents: [demo-data.md](demo-data.md).

## Incidents

1. Check `/live` vs `/ready` (process vs DB).
2. Grab `request_id` from the client error or `X-Request-ID`.
3. Search structured logs for that id.
4. Check `/metrics` for error and latency spikes (`signalflow_http_errors_total`, duration histograms).
5. If webhooks fail, verify signatures and provider dashboards before redeploying.

See also [monitoring.md](monitoring.md), [troubleshooting.md](troubleshooting.md), [deployment.md](deployment.md).
