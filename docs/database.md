# Database

## Engine

- PostgreSQL 16 (Compose image `postgres:16-alpine`)
- SQLAlchemy 2 declarative models in `backend/app/models/entities.py`
- Alembic revisions in `backend/alembic/versions/`

## Enums

| Type name | Values |
|-----------|--------|
| `userrole` | `owner`, `admin`, `member` |
| `integrationprovider` | `retell`, `twilio`, `calcom` |

Created explicitly once in `0001_initial`, then referenced with `create_type=False`.

## Tables

| Table | Purpose |
|-------|---------|
| `businesses` | Tenant root |
| `users` | Memberships / roles |
| `voice_agents` | Retell agent mapping |
| `knowledge_base_entries` | Q&A content |
| `callers` | Unique phone per business |
| `calls` | Call records (`retell_call_id` unique) |
| `appointments` | Bookings linked to caller/call |
| `integrations` | Provider credentials (encrypted column) |
| `webhook_events` | Idempotency store |

## Migrations

```bash
cd backend
alembic upgrade head
alembic current
alembic downgrade base   # drops tables, then enums
```

Compose backend command always runs `alembic upgrade head` before uvicorn.

## Reset

```bash
docker compose down -v
```

Removes the named volume `signalflow_postgres`.

## Dev tips

- Prefer migrations over `create_all` for schema changes that ship with the product.
- Tests use SQLAlchemy `create_all` against the test DB/engine configured in `tests/conftest.py`.
