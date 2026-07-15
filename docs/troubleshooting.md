# Troubleshooting

## `DuplicateObject: type "userrole" already exists`

Cause: Alembic enum created twice. Fixed in `0001_initial` via `postgresql.ENUM(..., create_type=False)`.

```bash
docker compose down -v
docker compose up --build
```

## Backend exits immediately after start

```bash
docker compose logs backend --tail 100
```

Common causes: migration failure, bad `SIGNALFLOW_DATABASE_URL`, missing `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` when saving integrations.

## Health check fails

```bash
curl -v http://localhost:8000/health
docker compose ps
```

## Dashboard empty / wrong tenant

Set `VITE_BUSINESS_ID` and recreate frontend:

```bash
docker compose up -d --force-recreate frontend
```

## Integration settings 401/503

| Code | Cause |
|------|-------|
| 401 | Missing or wrong `X-Owner-Token` / `X-Business-Id` |
| 503 | `OWNER_API_TOKEN` not configured in backend `.env` |
| 403 | Live mode without owner/admin user on business |

Set matching `VITE_OWNER_API_TOKEN` in frontend `.env`.

## Retell webhook 401 (live mode)

- Use raw request body for signature verification
- API key must have webhook badge in Retell dashboard
- Timestamp must be within 5 minutes

In mock mode, leave `RETELL_WEBHOOK_SECRET` empty or use legacy `sha256=` HMAC.

## Cal.com connection test fails

- Confirm `CALCOM_API_KEY` and `cal-api-version` header value
- Provide `CALCOM_EVENT_TYPE_ID` or slug + username
- Check API key scopes in Cal.com developer settings

## Integration routes fail in live mode

`INTEGRATION_MODE=live` requires all Retell/Cal.com credentials. Missing values raise clear errors from connection tests.

For local development, keep `INTEGRATION_MODE=mock`.

## Credential encryption error

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set as `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY`.

## Frontend build errors

```bash
cd frontend && npm ci && npx tsc --noEmit && npm run build
```

## Port already in use

Stop other Postgres/API processes or change Compose host ports.
