# API reference

Interactive docs: http://localhost:8000/docs when the API is running.

Base URL defaults to `http://localhost:8000`. There is no global `/api` router prefix beyond paths below.

## Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness — `{status, service, timestamp}` |

## Businesses

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/businesses` | Create business |
| `GET` | `/api/businesses/{business_id}` | Get business |
| `PATCH` | `/api/businesses/{business_id}` | Update business |

**Create body (example):** `name`, optional `industry`, `phone_number`, `forwarding_number`, `timezone`, `business_hours`, `service_area`.

## Knowledge base

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/businesses/{business_id}/knowledge-base` | Create entry |
| `GET` | `/api/businesses/{business_id}/knowledge-base` | List entries |
| `PATCH` | `/api/knowledge-base/{entry_id}` | Update entry |
| `DELETE` | `/api/knowledge-base/{entry_id}` | Delete entry |

## Calls

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/businesses/{business_id}/calls` | List calls (`limit` 1–200, default 50) |
| `GET` | `/api/calls/{call_id}` | Get call (`business_id` query required) |

## Appointments

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/businesses/{business_id}/appointments` | List |
| `POST` | `/api/appointments` | Create |
| `PATCH` | `/api/appointments/{appointment_id}` | Update (`business_id` query required) |

## Integrations (mock mode)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/integrations/calcom/availability` | Slot list |
| `POST` | `/api/integrations/calcom/book` | Book appointment slot |
| `POST` | `/api/integrations/twilio/send-summary` | Send SMS summary |

When mocks are disabled, these return **501**.

## Webhooks

| Method | Path | Header | Description |
|--------|------|--------|-------------|
| `POST` | `/api/webhooks/retell/call-started` | `X-Retell-Signature` | Start call record |
| `POST` | `/api/webhooks/retell/call-ended` | `X-Retell-Signature` | Complete call + optional appointment |
| `POST` | `/api/webhooks/calcom` | `X-Cal-Signature` | Ack / idempotency claim |

HMAC is enforced only when the matching secret env var is non-empty.

## Tenancy note

Until authentication ships, callers must supply `business_id` correctly. Endpoints still validate relational ownership for appointments and call reads.
