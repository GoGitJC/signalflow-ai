# Environment variables

Copy `.env.example` to `.env` for local work. **Never commit `.env`.** (`.env` and `.env.*` are gitignored.)

## Integration mode

| Variable | Default | Description |
|----------|---------|-------------|
| `INTEGRATION_MODE` | `mock` | `mock` keeps provider adapters local; `live` requires credentials below |
| `APP_PUBLIC_API_URL` | `http://localhost:8000` | Public API base for webhook URLs |
| `OWNER_API_TOKEN` | empty | Required for integration settings endpoints (`X-Owner-Token`) |

`INTEGRATION_MODE=mock` sets `SIGNALFLOW_MOCK_EXTERNAL_SERVICES=true`.

## Retell AI

| Variable | Default | Live required |
|----------|---------|---------------|
| `RETELL_API_KEY` | empty | Yes |
| `RETELL_AGENT_ID` | empty | No (resolved by name if omitted) |
| `RETELL_AGENT_NAME` | `Universal_Demo` | Yes (exact match) |
| `RETELL_WEBHOOK_BASE_URL` | empty | No (falls back to `APP_PUBLIC_API_URL`) |
| `RETELL_WEBHOOK_SECRET` | empty | Mock legacy HMAC only |

Legacy alias: `SIGNALFLOW_RETELL_WEBHOOK_SECRET`.

## Cal.com API v2

| Variable | Default | Live required |
|----------|---------|---------------|
| `CALCOM_API_KEY` | empty | Yes |
| `CALCOM_API_BASE_URL` | `https://api.cal.com/v2` | Yes |
| `CALCOM_API_VERSION` | `2024-09-04` | Yes |
| `CALCOM_EVENT_TYPE_ID` | empty | One of ID or slug+username |
| `CALCOM_EVENT_TYPE_SLUG` | empty | With `CALCOM_USERNAME` |
| `CALCOM_USERNAME` | empty | With slug |

Legacy alias: `SIGNALFLOW_CALCOM_WEBHOOK_SECRET` for Cal.com webhook HMAC.

## Backend (SIGNALFLOW_ prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGNALFLOW_ENVIRONMENT` | `development` | Environment label |
| `SIGNALFLOW_DATABASE_URL` | Compose internal URL | SQLAlchemy URL |
| `SIGNALFLOW_FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow-origin |
| `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` | empty | Fernet key — required to save per-business credentials |
| `SIGNALFLOW_TWILIO_ACCOUNT_SID` | empty | Reserved |
| `SIGNALFLOW_TWILIO_AUTH_TOKEN` | empty | Reserved |

## Ops / production readiness

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_JSON` | `true` | Structured JSON logs |
| `RATE_LIMIT_ENABLED` | `true` | Auth/webhook rate limiting |
| `JWT_SECRET` | empty | Required for cookie sessions; fail-fast in production |
| `AUTH_COOKIE_SECURE` | `false` | Must be `true` in production |

Production (`SIGNALFLOW_ENVIRONMENT=production`) also requires encryption key, non-localhost `SIGNALFLOW_FRONTEND_ORIGIN`, and secure cookies.

## Frontend (VITE_ prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | API base URL |
| `VITE_BUSINESS_ID` | empty | Optional default tenant hint for local/demo |

Dashboard auth uses HttpOnly cookies — do not put JWTs or owner tokens in frontend env.

## Live mode startup

When `INTEGRATION_MODE=live`:

- Retell connection tests require `RETELL_API_KEY`
- Cal.com connection tests require `CALCOM_API_KEY` and resolvable event type
- Retell webhooks require valid `X-Retell-Signature` (API key verification)
- Owner integration routes require `OWNER_API_TOKEN` and an owner/admin user in live mode

## Secrets hygiene

- Do not put real provider keys in commits, docs, screenshots, or chat
- Rotate credentials after exposure
- Use platform secret stores in production
