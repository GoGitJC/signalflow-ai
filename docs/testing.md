# Testing

## Backend (Docker — recommended)

```bash
docker compose run --rm backend-test sh -c "ruff check . && mypy app && pytest -q"
```

## Backend (local venv)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
mypy app
pytest
```

## Test coverage

| Suite | Focus |
|-------|-------|
| `test_retell_webhook.py` | Call-ended flow, idempotency, tenant scope |
| `test_retell_integration.py` | Agent resolution, signatures, connection test, cross-tenant |
| `test_calcom_integration.py` | Event type resolution, slots, booking, webhooks, duplicates |
| `test_live_flow.py` | Tool schemas, envelope unwrap, confirmation gate, live booking guard, tenants |
| `test_e2e_integration_flow.py` | Mocked call → availability → book → dashboard |
| `test_mock_integrations.py` | Legacy mock Cal.com/Twilio routes |

All provider HTTP calls are mocked — tests do not consume paid Retell or Cal.com usage.

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

## Conventions

- `INTEGRATION_MODE=mock` in `conftest.py`
- Fernet test key and `OWNER_API_TOKEN` set for integration settings tests
- Deterministic webhook fixtures with legacy HMAC in mock mode
- No real credentials in fixtures or assertions
## Integration verification

```bash
docker compose run --rm backend-test sh -c "ruff check . && ruff format --check . && mypy app && pytest -q"
./scripts/verify_integrations.sh
```
