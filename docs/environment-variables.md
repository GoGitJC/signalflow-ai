# Environment variables

All backend settings use the `SIGNALFLOW_` prefix (Pydantic Settings). Frontend vars use the `VITE_` prefix.

Copy `.env.example` to `.env` for local work. **Never commit `.env`.**

## Backend

| Variable | Default / example | Required | Description |
|----------|-------------------|----------|-------------|
| `SIGNALFLOW_ENVIRONMENT` | `development` | No | Environment label |
| `SIGNALFLOW_DATABASE_URL` | Compose sets `postgresql+psycopg://signalflow:signalflow@db:5432/signalflow` | Yes (runtime) | SQLAlchemy URL |
| `SIGNALFLOW_FRONTEND_ORIGIN` | `http://localhost:5173` | Yes | CORS allow-origin |
| `SIGNALFLOW_MOCK_EXTERNAL_SERVICES` | `true` | No | Use mock Cal.com/Twilio; `false` returns 501 for live routes |
| `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` | empty | Later | Fernet/key material for encrypted integration credentials |
| `SIGNALFLOW_RETELL_WEBHOOK_SECRET` | empty | Prod Retell | When set, requires valid `X-Retell-Signature` |
| `SIGNALFLOW_CALCOM_WEBHOOK_SECRET` | empty | Prod Cal.com | When set, requires valid `X-Cal-Signature` |
| `SIGNALFLOW_TWILIO_ACCOUNT_SID` | empty | Live Twilio | Reserved |
| `SIGNALFLOW_TWILIO_AUTH_TOKEN` | empty | Live Twilio | Reserved |

Loaded from `.env` in the API process working directory (`backend/` or container `/app`).

## Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | API base URL (Compose sets this) |
| `VITE_BUSINESS_ID` | empty | Tenant ID for the dashboard in this MVP phase |

`VITE_BUSINESS_ID` can also be stored in `localStorage` key `signalflow_business_id`.

## Compose interaction

`docker-compose.yml` loads root `.env` for the backend and overrides `SIGNALFLOW_DATABASE_URL` to the internal `db` hostname. Frontend receives `VITE_API_URL` and optional `VITE_BUSINESS_ID`.

## Secrets hygiene

- Do not put real provider keys in commits, screenshots, or issue templates.
- Rotate any credential that was pasted into chat, CI logs, or a public gist.
- Prefer platform secret stores for production.
