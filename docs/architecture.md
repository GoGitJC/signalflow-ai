# Architecture

## Purpose

SignalFlow AI is a multi-tenant platform that connects voice AI (Retell), telephony/SMS (Twilio), and scheduling (Cal.com) to a business-scoped PostgreSQL data model and operator dashboard.

## High-level components

| Component | Path | Role |
|-----------|------|------|
| API server | `backend/app` | REST APIs, webhook ingress, CORS, error handling |
| Persistence | `backend/app/models`, Alembic | Tenant-scoped entities and migrations |
| Services | `backend/app/services` | Completed-call orchestration and idempotency |
| Integrations | `backend/app/integrations` | Mock (and later live) provider clients |
| Dashboard | `frontend/src` | Operator UI bound to a business ID |
| Compose | `docker-compose.yml` | Local Postgres + API + Vite |

## Request paths

1. **Dashboard CRUD/read** — React client → FastAPI routes → SQLAlchemy session → PostgreSQL.
2. **Retell webhooks** — Provider → `POST /api/webhooks/retell/*` → HMAC (optional) → idempotency claim → call/caller/appointment persistence.
3. **Mock integrations** — API routes → `MockCalComClient` / `MockTwilioClient` when `SIGNALFLOW_MOCK_EXTERNAL_SERVICES=true`.

## Tenancy model

Every business entity (`users`, `voice_agents`, `knowledge_base_entries`, `callers`, `calls`, `appointments`, `integrations`) carries `business_id`. In this MVP phase the client supplies that ID. Production auth (Phase 2) must resolve membership server-side.

## Idempotency

`webhook_events` stores `(provider, event_key)` unique pairs. Retell and Cal.com handlers claim events before mutating domain data to safely handle retries.

## Enum types

PostgreSQL enums created once by Alembic:

- `userrole` — `owner`, `admin`, `member`
- `integrationprovider` — `retell`, `twilio`, `calcom`

Migration uses `postgresql.ENUM(..., create_type=False)` after an explicit `.create()` so types are not duplicated on `CREATE TABLE`.

## Frontend structure

Single-page shell (`App.tsx`) with view state for Overview, Calls, Appointments, Knowledge Base, and Settings. Typed client in `frontend/src/api/client.ts`.

## Security boundaries

Documented in [security.md](security.md). Summary: no auth yet; webhook HMAC when secrets configured; encrypted credential column reserved for later phases.
