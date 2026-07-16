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

## Auth (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create business + owner user; returns JWT pair |
| `POST` | `/api/auth/login` | Email/password → JWT pair |
| `POST` | `/api/auth/refresh` | Rotate refresh token → new JWT pair |
| `GET` | `/api/auth/me` | Current user (Bearer access token) |

Integration admin routes accept `Authorization: Bearer <access_token>` (owner/admin). Legacy `X-Owner-Token` + `X-Business-Id` remain supported during migration.

## Integrations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/integrations/retell/status` | Owner | Masked Retell status |
| `PUT` | `/api/integrations/retell` | Owner | Upsert Retell credentials |
| `POST` | `/api/integrations/retell/test` | Owner | Connection test |
| `GET` | `/api/integrations/calcom/status` | Owner | Masked Cal.com status |
| `PUT` | `/api/integrations/calcom` | Owner | Upsert Cal.com credentials |
| `POST` | `/api/integrations/calcom/test` | Owner | Connection test |
| `POST` | `/api/integrations/calcom/availability` | Owner | Slot list |
| `POST` | `/api/integrations/calcom/book` | Owner | Book appointment slot |
| `POST` | `/api/integrations/twilio/send-summary` | — | Send SMS summary |

Owner routes require `X-Owner-Token` and `X-Business-Id`. Live Cal.com booking also requires `ALLOW_LIVE_BOOKING=true`.

## Retell voice tools

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/retell/tools/check_availability` | Voice-friendly slots via agent → business mapping |
| `POST` | `/api/retell/tools/book_appointment` | Book after `caller_confirmed=true` |

Accepts either a flat JSON body or Retell's `{ "call", "name", "args" }` envelope.

## Webhooks

| Method | Path | Header | Description |
|--------|------|--------|-------------|
| `POST` | `/api/webhooks/retell/call-started` | `X-Retell-Signature` | Start call record |
| `POST` | `/api/webhooks/retell/call-ended` | `X-Retell-Signature` | Complete call + optional appointment |
| `POST` | `/api/webhooks/calcom` | `X-Cal-Signature` | Ack / idempotency claim |

HMAC is enforced only when the matching secret env var is non-empty.

## Tenancy note

Until authentication ships, callers must supply `business_id` correctly. Endpoints still validate relational ownership for appointments and call reads.
