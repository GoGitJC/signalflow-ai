# Testing

## Backend (pytest + ruff + mypy)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest
```

Tests live in `backend/tests/` and cover health, business/KB, mock integrations, and Retell webhook flows (including idempotency and tenant isolation scenarios).

## Frontend

```bash
cd frontend
npm ci
npx tsc --noEmit
npm run build
```

## Docker smoke

```bash
docker compose down -v
docker compose up --build -d
curl -sf http://localhost:8000/health
docker compose ps
```

## CI

`.github/workflows/ci.yml` runs formatting, lint, typing, backend tests, frontend typecheck/build, and Docker image builds on pull requests and pushes to `main`.

## Conventions

- Prefer API-level tests with FastAPI `TestClient`.
- Keep webhook fixtures deterministic.
- Do not require external network for unit/integration tests — mocks are the default.
