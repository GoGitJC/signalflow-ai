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

**Lifecycle (required):**

1. Alembic creates each PostgreSQL enum once via `postgresql.ENUM(...).create(..., checkfirst=True)`.
2. Table DDL references the same types with `create_type=False` so `CREATE TABLE` does not emit a second `CREATE TYPE`.
3. ORM columns in `entities.py` also use named enums with `create_type=False` so `metadata.create_all` (tests) never fights Alembic on PostgreSQL.
4. Downgrade drops tables first, then enum types.

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
