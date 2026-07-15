# Local development

## Prerequisites

- Docker Desktop (or compatible Compose v2)
- Optional: Python 3.12+, Node.js 20+ for host-side tooling

## Start the stack

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | Port | Notes |
|---------|------|-------|
| `db` | 5432 | Postgres 16, healthchecked |
| `backend` | 8000 | runs `alembic upgrade head` then uvicorn |
| `frontend` | 5173 | Vite dev server |

Verify:

```bash
curl -sS http://localhost:8000/health
docker compose ps
```

## Seed a business and simulate a call

```bash
curl -sS -X POST http://localhost:8000/api/businesses \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo HVAC","industry":"hvac"}'
```

Set `VITE_BUSINESS_ID` in `.env` to the returned UUID, then:

```bash
docker compose up -d --force-recreate frontend
BUSINESS_ID=<uuid> ./scripts/simulate_call.sh
```

Open http://localhost:5173 — you should see the call and appointment.

## Backend without Docker

Requires a reachable Postgres matching `SIGNALFLOW_DATABASE_URL`.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export SIGNALFLOW_DATABASE_URL=postgresql+psycopg://signalflow:signalflow@localhost:5432/signalflow
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Frontend without Docker

```bash
cd frontend
npm ci
VITE_API_URL=http://localhost:8000 VITE_BUSINESS_ID=<uuid> npm run dev
```

## Reset database

```bash
docker compose down -v
docker compose up --build
```

Volumes are destroyed; Alembic recreates the schema from `0001_initial`.

## Useful URLs

- OpenAPI UI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Dashboard: http://localhost:5173
