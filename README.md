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
- **Frontend** (`frontend/`): Vite + React + TypeScript dashboard with TanStack Query — CRM customers, call intelligence, appointments, analytics, voice agent, knowledge base, settings.
- **Integrations**: Mock providers by default (`INTEGRATION_MODE=mock`). Live Retell/Cal.com clients are supported when `INTEGRATION_MODE=live`; real Cal.com bookings stay gated by `ALLOW_LIVE_BOOKING=false` until explicitly enabled.
- **Data**: PostgreSQL 16 with enum-backed domain types (`userrole`, `integrationprovider`).

See [docs/architecture.md](docs/architecture.md) for deeper detail.

## Technology stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Pydantic Settings, Uvicorn |
| ORM / DB | SQLAlchemy 2, Alembic, PostgreSQL 16, psycopg3 |
| Dashboard | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Providers | Retell (webhooks), Twilio (SMS), Cal.com (scheduling) — mocked locally |
| Ops | Docker Compose, GitHub Actions CI |

## Quick start (local)

```bash
cp .env.example .env
./scripts/dev-up.sh
# reset DB volume if needed: ./scripts/dev-up.sh --reset
```

| Service | URL |
|---------|-----|
| API + OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Ready | http://localhost:8000/ready |
| Live | http://localhost:8000/live |
| Metrics | http://localhost:8000/metrics |
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
| `INTEGRATION_MODE` | `mock` (default) or `live` for Retell/Cal.com adapters |
| `APP_PUBLIC_API_URL` | Public API URL for webhook registration |
| `OWNER_API_TOKEN` | Optional bootstrap/CLI owner token (dashboard uses cookies) |
| `JWT_SECRET` | Required for cookie/JWT sessions |
| `LOG_LEVEL` / `LOG_JSON` | Logging level and JSON format |
| `RATE_LIMIT_ENABLED` | Auth/webhook rate limiting |
| `RETELL_API_KEY`, `RETELL_AGENT_ID`, `RETELL_AGENT_NAME` | Retell live credentials |
| `CALCOM_API_KEY`, `CALCOM_EVENT_TYPE_ID`, `CALCOM_EVENT_TYPE_SLUG`, `CALCOM_USERNAME` | Cal.com live credentials |
| `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY` | Fernet key for encrypted integration secrets |
| `SIGNALFLOW_RETELL_WEBHOOK_SECRET` | Mock legacy HMAC for Retell webhooks |
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

Production `backend` image stays minimal (no ruff/mypy/pytest). Use the Compose **`backend-test`** service (Dockerfile `development` target + `[dev]` extras):

```bash
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test ruff format --check .
docker compose run --rm backend-test mypy .
docker compose run --rm backend-test pytest
```

`backend-test` mounts `./backend`, installs the `dev` dependency group, and can reach Postgres at `db:5432` when tests need it (current suite uses in-memory SQLite).

Host-side alternative:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy .
pytest
```

Frontend (with stack running):

```bash
docker compose exec frontend npm run build
```

### Full verification suite

```bash
docker compose down -v
docker compose up --build -d
docker compose ps
curl -i http://localhost:8000/health
curl -i http://localhost:8000/live
curl -i http://localhost:8000/ready
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test ruff format --check .
docker compose run --rm backend-test mypy .
docker compose run --rm backend-test pytest
docker compose exec frontend npm run build
```

See [docs/testing.md](docs/testing.md).

## Mock providers

With `INTEGRATION_MODE=mock` (default):

- Retell and Cal.com connection tests return mocked success
- `POST /api/integrations/calcom/availability` — synthetic hourly slots
- `POST /api/integrations/calcom/book` — transactional mock bookings
- `POST /api/retell/tools/check_availability` and `/book_appointment` — agent-scoped scheduling
- Retell webhooks accept unsigned bodies when secrets are empty

Set `INTEGRATION_MODE=live` with provider credentials for real API calls (see integration docs).

Simulate a completed call:

```bash
BUSINESS_ID=<uuid> ./scripts/simulate_call.sh
```

### Live-ready integration verification

```bash
python scripts/prepare_integration_keys.py
docker compose exec backend python -m app.cli.sync_live_integrations --business-id "$VITE_BUSINESS_ID"
./scripts/verify_integrations.sh
```

`ALLOW_LIVE_BOOKING` defaults to `false`. Do not enable it until an operator approves a real booking with valid customer information.

Latest controlled acceptance notes: [docs/integrations/live-acceptance-2026-07-16.md](docs/integrations/live-acceptance-2026-07-16.md)  
(Retell + availability + webhooks + dashboard verified; final live booking is a production checklist item).

Final release booking checks: [docs/production-readiness.md](docs/production-readiness.md#final-production-acceptance-checklist).

Provider docs: [Retell](docs/integrations/retell.md) · [Twilio](docs/integrations/twilio.md) · [Cal.com](docs/integrations/calcom.md).

## Deployment overview

Local and CI use Dockerfiles under `backend/` and `frontend/`. Production deployment (managed Postgres, secrets, TLS, reverse proxy) is documented in [docs/deployment.md](docs/deployment.md) and readiness criteria in [docs/production-readiness.md](docs/production-readiness.md).

## Screenshots

Customer experience captures (Phase 3):

| Shot | Path | Notes |
|------|------|-------|
| Overview | [`docs/images/cx-overview.png`](docs/images/cx-overview.png) | Executive stats + charts |
| Customers | [`docs/images/cx-customers.png`](docs/images/cx-customers.png) | CRM directory |
| Calls | [`docs/images/cx-calls.png`](docs/images/cx-calls.png) | Call intelligence list |
| Analytics | [`docs/images/cx-analytics.png`](docs/images/cx-analytics.png) | Funnel + ranges |
| Knowledge | [`docs/images/cx-knowledge.png`](docs/images/cx-knowledge.png) | KB editor |

UI system documentation: [docs/ui.md](docs/ui.md). Product surface: [docs/dashboard.md](docs/dashboard.md).

## Security notes

- Dashboard auth uses HttpOnly cookie sessions (`sf_access` / `sf_refresh`) with automatic refresh. JWTs are not stored in `localStorage`.
- Tenant `business_id` on protected routes must match the authenticated membership.
- Webhook HMAC is enforced when the corresponding secret is configured.
- Never commit `.env`, dumps, or provider credentials.

See [docs/security.md](docs/security.md), [docs/auth.md](docs/auth.md), and [SECURITY.md](SECURITY.md).

## Known limitations

- Email delivery for verification/reset/invite is stubbed (tokens returned in API responses for local/dev).
- Multi-business memberships beyond a single `users.business_id` are planned.
- Live Twilio HTTP client is not fully productionized; confirmation SMS is on the Final Production Acceptance Checklist.
- Final live booking with valid customer data is a **release checklist** item (keep `ALLOW_LIVE_BOOKING=false` until then).
- Pagination and heavy async job queues remain future work; baseline metrics/logging/rate limits are in place.

## Roadmap

Tracked in [PHASES.md](PHASES.md). Core product + Phase 5 production readiness are the current focus for first-customer launch. Keep `ALLOW_LIVE_BOOKING=false` until Final Production Acceptance.

## Documentation index

| Doc | Description |
|-----|-------------|
| [Architecture](docs/architecture.md) | System design |
| [Local development](docs/local-development.md) | Day-to-day setup |
| [Deployment](docs/deployment.md) | Containers and hosting (Render/Railway/DO/AWS) |
| [Operations](docs/operations.md) | Backups, restore, probes, rate limits |
| [Monitoring](docs/monitoring.md) | Metrics and alerts |
| [Onboarding](docs/onboarding.md) | First-run customer setup |
| [Demo data](docs/demo-data.md) | HVAC demo seed |
| [Release notes (v1.0 Beta)](docs/RELEASE_NOTES_v1.0_BETA.md) | Closed-beta release notes |
| [Environment variables](docs/environment-variables.md) | Config reference |
| [API](docs/api.md) | HTTP surface |
| [Database](docs/database.md) | Schema and migrations |
| [Auth](docs/auth.md) | Sessions and roles |
| [Security](docs/security.md) | CORS, cookies, CSP, secrets |
| [Testing](docs/testing.md) | Test and CI commands |
| [Troubleshooting](docs/troubleshooting.md) | Common failures |
| [Production readiness](docs/production-readiness.md) | Go-live checklist |
| [Contributing](CONTRIBUTING.md) | PR / commit process |
| [Changelog](CHANGELOG.md) | Release history |

## License

See [LICENSE](LICENSE).
