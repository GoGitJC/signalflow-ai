# SignalFlow AI

Multi-tenant AI receptionist platform for service businesses. SignalFlow answers inbound calls, captures lead intent, books appointments, and gives operators a dashboard for calls, appointments, and knowledge-base content.

This repository is the production-oriented MVP foundation: FastAPI + PostgreSQL backend, React dashboard, Docker Compose local stack, and mock Retell / Twilio / Cal.com adapters for a complete offline completed-call path.

## Architecture overview

```text
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│ React / Vite │────▶│ FastAPI (backend)  │────▶│ PostgreSQL   │
│ dashboard    │     │ REST + webhooks    │     │ + Alembic    │
└──────────────┘     └─────────┬──────────┘     └──────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
           Retell AI        Twilio SMS       Cal.com
          (webhooks)       (mock/SMS)     (avail/book)
```

- **Backend** (`backend/`): FastAPI app, SQLAlchemy models, Alembic migrations, webhook processing, tenant-scoped APIs.
- **Frontend** (`frontend/`): Vite + React + TypeScript dashboard (overview, calls, appointments, knowledge base, settings).
- **Integrations**: Mock providers by default (`SIGNALFLOW_MOCK_EXTERNAL_SERVICES=true`). Live clients are phased for later work.
- **Data**: PostgreSQL 16 with enum-backed domain types (`userrole`, `integrationprovider`).

See [docs/architecture.md](docs/architecture.md) for deeper detail.

## Technology stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Pydantic Settings, Uvicorn |
| ORM / DB | SQLAlchemy 2, Alembic, PostgreSQL 16, psycopg3 |
| Dashboard | React 18+, TypeScript, Vite, Tailwind CSS |
| Providers | Retell (webhooks), Twilio (SMS), Cal.com (scheduling) — mocked locally |
| Ops | Docker Compose, GitHub Actions CI |

## Quick start (local)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| API + OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Dashboard | http://localhost:5173 |

Create a business and wire the dashboard:

```bash
curl -sS -X POST http://localhost:8000/api/businesses \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alamo Dental Services","industry":"dental"}'
```

Copy the returned `id` into `.env` as `VITE_BUSINESS_ID`, recreate the frontend, then simulate a call:

```bash
docker compose up -d --force-recreate frontend
BUSINESS_ID=<returned-id> ./scripts/simulate_call.sh
```

Full walkthrough: [docs/local-development.md](docs/local-development.md).

## Environment variables

Copy `.env.example` → `.env`. Never commit `.env`.

| Variable | Purpose |
|----------|---------|
| `SIGNALFLOW_ENVIRONMENT` | `development` / `production` |
| `SIGNALFLOW_DATABASE_URL` | SQLAlchemy URL (Compose overrides to the `db` service) |
| `SIGNALFLOW_FRONTEND_ORIGIN` | CORS origin for the dashboard |
| `SIGNALFLOW_MOCK_EXTERNAL_SERVICES` | `true` enables mock Cal.com / Twilio |
| `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` | Reserved for encrypted integration secrets |
| `SIGNALFLOW_RETELL_WEBHOOK_SECRET` | Optional HMAC for Retell webhooks |
| `SIGNALFLOW_CALCOM_WEBHOOK_SECRET` | Optional HMAC for Cal.com webhooks |
| `SIGNALFLOW_TWILIO_ACCOUNT_SID` / `SIGNALFLOW_TWILIO_AUTH_TOKEN` | Reserved for live Twilio |
| `VITE_API_URL` | Frontend API base (default `http://localhost:8000`) |
| `VITE_BUSINESS_ID` | Dashboard tenant context for this MVP phase |

Details: [docs/environment-variables.md](docs/environment-variables.md).

## Database migrations

Compose runs migrations on backend start:

```bash
alembic upgrade head
```

Manual (inside backend / venv):

```bash
cd backend
alembic upgrade head
alembic downgrade -1   # drop tables then enum types
```

Schema notes: [docs/database.md](docs/database.md).

## Tests and quality checks

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest

# Frontend
cd frontend
npm ci
npx tsc --noEmit
npm run build
```

See [docs/testing.md](docs/testing.md).

## Mock providers

With `SIGNALFLOW_MOCK_EXTERNAL_SERVICES=true` (default):

- `POST /api/integrations/calcom/availability` — synthetic hourly slots
- `POST /api/integrations/calcom/book` — mock event IDs
- `POST /api/integrations/twilio/send-summary` — queued mock SMS
- Retell webhooks accept unsigned bodies when secrets are empty

Simulate a completed call:

```bash
BUSINESS_ID=<uuid> ./scripts/simulate_call.sh
```

Provider docs: [Retell](docs/integrations/retell.md) · [Twilio](docs/integrations/twilio.md) · [Cal.com](docs/integrations/calcom.md).

## Deployment overview

Local and CI use Dockerfiles under `backend/` and `frontend/`. Production deployment (managed Postgres, secrets, TLS, reverse proxy) is documented in [docs/deployment.md](docs/deployment.md) and readiness criteria in [docs/production-readiness.md](docs/production-readiness.md).

## Screenshots

> Screenshots will be added under `docs/images/` as the dashboard UI stabilizes.
>
> Suggested captures: Overview, Calls table with transcript expand, Appointments, Knowledge base editor, Settings.

## Security notes

- This phase has **no login**. Tenant context is supplied in paths/queries; APIs still enforce tenant isolation on reads/writes.
- Production must derive `business_id` from authenticated membership, not client trust.
- Webhook HMAC is enforced when the corresponding secret is configured.
- Never commit `.env`, dumps, or provider credentials.

See [docs/security.md](docs/security.md) and [SECURITY.md](SECURITY.md).

## Known limitations

- No authentication / RBAC enforcement yet (models include `User` / `UserRole`).
- Live Retell / Twilio / Cal.com HTTP clients are not enabled (`501` when mocks are off).
- Frontend settings are read-only; no credential CRUD UI.
- Pagination, audit logs, async jobs, and observability are planned later phases.

## Roadmap

Tracked in [PHASES.md](PHASES.md):

1. Foundation + simulated completed-call flow *(current baseline)*
2. Authentication and tenant authorization
3. Provider integration architecture
4. Receptionist orchestration
5. Production dashboard
6. Async processing and observability
7. Deployment and operations

## Documentation index

| Doc | Description |
|-----|-------------|
| [Architecture](docs/architecture.md) | System design |
| [Local development](docs/local-development.md) | Day-to-day setup |
| [Deployment](docs/deployment.md) | Containers and hosting |
| [Environment variables](docs/environment-variables.md) | Config reference |
| [API](docs/api.md) | HTTP surface |
| [Database](docs/database.md) | Schema and migrations |
| [Testing](docs/testing.md) | Test and CI commands |
| [Troubleshooting](docs/troubleshooting.md) | Common failures |
| [Production readiness](docs/production-readiness.md) | Go-live checklist |
| [Contributing](CONTRIBUTING.md) | PR / commit process |
| [Changelog](CHANGELOG.md) | Release history |

## License

See [LICENSE](LICENSE).
