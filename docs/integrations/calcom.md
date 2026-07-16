# Cal.com integration

## Role

Cal.com API v2 provides availability and booking. SignalFlow stores booking UIDs as `cal_event_id` and syncs status from webhooks.

## Credentials

| Variable | Purpose |
|----------|---------|
| `CALCOM_API_KEY` | Bearer token for API v2 |
| `CALCOM_API_BASE_URL` | Default `https://api.cal.com/v2` |
| `CALCOM_API_VERSION` | Required `cal-api-version` header (default `2024-09-04`) |
| `CALCOM_EVENT_TYPE_ID` | Resolve event type by ID |
| `CALCOM_EVENT_TYPE_SLUG` + `CALCOM_USERNAME` | Resolve event type by slug |
| `INTEGRATION_MODE` | `mock` (default) or `live` |

Per-business credentials are encrypted in `integrations` (provider `calcom`).

## Create a Cal.com API key

1. Open [Cal.com settings → Developer](https://app.cal.com/settings/developer)
2. Create an API key
3. Store as `CALCOM_API_KEY` in `.env`

## Find event type ID or slug

- Event type ID: Cal.com event type settings URL or `GET /v2/event-types`
- Slug + username: public booking link `https://cal.com/{username}/{slug}`

## Management API (owner/admin)

Headers: `X-Owner-Token`, `X-Business-Id`

| Method | Path |
|--------|------|
| `GET` | `/api/integrations/calcom/status` |
| `PUT` | `/api/integrations/calcom` |
| `POST` | `/api/integrations/calcom/test` |
| `POST` | `/api/integrations/calcom/availability` |
| `POST` | `/api/integrations/calcom/book` |

## Scheduling API

`availability` and `book` require the same owner headers. Body `business_id` must match `X-Business-Id`.

| Method | Path | Mode |
|--------|------|------|
| `POST` | `/api/integrations/calcom/availability` | mock + live |
| `POST` | `/api/integrations/calcom/book` | mock + live (`ALLOW_LIVE_BOOKING=true`) |

Live booking uses `POST /v2/bookings` with:

- `eventTypeId` or `username` + `eventTypeSlug`
- `start` (ISO UTC)
- `attendee` (`name`, `email`, `timeZone`, optional `phoneNumber`)
- `metadata.service`

Bookings are transactional: local appointments are not confirmed unless Cal.com succeeds. Duplicate protection uses a local idempotency hash.

## Webhook

| Method | Path | Header |
|--------|------|--------|
| `POST` | `/api/webhooks/calcom` | `X-Cal-Signature` |

When `SIGNALFLOW_CALCOM_WEBHOOK_SECRET` is set, HMAC-SHA256 of the raw body is required. Matching appointments update `status` by booking UID.

## Test availability without booking

```bash
curl -X POST http://localhost:8000/api/integrations/calcom/availability \
  -H "Content-Type: application/json" \
  -H "X-Owner-Token: $OWNER_API_TOKEN" \
  -H "X-Business-Id: $VITE_BUSINESS_ID" \
  -d '{
    "business_id": "<uuid>",
    "start": "2026-08-01T00:00:00Z",
    "end": "2026-08-02T00:00:00Z"
  }'
```

In live mode this calls `GET /v2/slots` with `cal-api-version: 2024-09-04`.

## API versions

| Endpoint family | Suggested `cal-api-version` |
|-----------------|----------------------------|
| Slots | `2024-09-04` |
| Bookings | `2024-08-13` |

`CALCOM_API_VERSION` is sent on metadata requests; slots and bookings use the versions required by Cal.com v2 docs.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| 401 Unauthorized | API key and Bearer header |
| 404 on v2 routes | Missing `cal-api-version` header |
| Ambiguous event type | Set `CALCOM_EVENT_TYPE_ID` explicitly |
| Booking conflict | Slot taken — pick another slot |

## Production checklist

- [ ] Connection test passes
- [ ] Event type resolved uniquely
- [ ] Webhook secret configured
- [ ] Availability tested for a future date range (no booking)
- [ ] Real booking only after explicit approval

## Live booking guard

`ALLOW_LIVE_BOOKING=false` (default) blocks remote Cal.com booking calls even when `INTEGRATION_MODE=live`.
Set `ALLOW_LIVE_BOOKING=true` only after explicit approval to create real bookings.

Event type listing/get requires `CALCOM_EVENT_TYPES_API_VERSION=2024-06-14`.

## Manual availability check

```bash
./scripts/verify_integrations.sh
```

Uses a ~14-day future window and never creates a booking.

Live acceptance notes (booking gate + Cal.com 400 investigation): [live-acceptance-2026-07-16.md](./live-acceptance-2026-07-16.md).
