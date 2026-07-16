# Disaster recovery

Procedures for SignalFlow AI production (Render Postgres + Render API + Vercel frontend).

## RTO / RPO targets (initial)

| Metric | Initial target |
|--------|----------------|
| RPO (data loss window) | ≤ 24h (improve with PITR if plan allows) |
| RTO (time to restore service) | ≤ 4h for first customer |

## Backup

### Managed (preferred)

1. Render Dashboard → PostgreSQL → **Backups**
2. Enable automatic backups (plan-dependent)
3. Confirm retention (minimum 7 days for beta)

### Manual logical dump

From a machine with network access to the DB (prefer temporary allowlist):

```bash
pg_dump "$DATABASE_URL" --format=custom --file="signalflow-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Store encrypted off-platform (object storage with SSE).

## Restore

1. Announce maintenance; scale API to 0 or enable maintenance page on Vercel
2. Create a new Render Postgres instance **or** restore into existing per Render UI
3. Restore dump if using logical backup:

```bash
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" signalflow-YYYYMMDD.dump
```

4. Point `SIGNALFLOW_DATABASE_URL` at the restored database
5. Deploy / restart API (`alembic upgrade head` is safe if already at head)
6. Verify:

```bash
curl -fsS https://api.<DOMAIN>/ready
curl -fsS https://api.<DOMAIN>/live
```

7. Sign in on `https://www.<DOMAIN>` and spot-check calls/appointments
8. Re-enable traffic

## Migration rollback

1. Take a fresh backup **before** every production migration
2. Prefer forward-fix migrations
3. If required:

```bash
# one-off Render shell / job in backend container
alembic downgrade -1
```

4. Redeploy the application image that matches the schema revision
5. Verify `/ready` and auth cookies

Never downgrade past irreversible data deletes without a restore.

## Application rollback

### API (Render)

1. Render → service → **Events** / deploys → **Rollback** to previous successful deploy
2. Or redeploy previous Git SHA
3. Confirm `/ready` and webhook delivery

### Frontend (Vercel)

1. Vercel → Deployments → promote previous Production deployment
2. Confirm `VITE_API_URL` still points at the intended API

## Region / provider outage

1. Status pages: Render, Vercel, Cloudflare, Retell, Cal.com, Twilio
2. If API down but DB up: wait for Render recovery or restore DB to new instance and re-point service
3. If only frontend down: Vercel rollback / redeploy; API can still serve webhooks
4. Communicate status to the customer contact

## Secrets compromise

1. Rotate `JWT_SECRET` (forces re-login), Fernet encryption key **only with a planned re-encrypt**, provider API keys, webhook secrets
2. Revoke `OWNER_API_TOKEN`
3. Review audit log exports
4. See [../security.md](../security.md)

## Contact tree

Fill before go-live:

| Role | Name | Contact |
|------|------|---------|
| Deploy approver | | |
| On-call engineer | | |
| Customer success | | |
