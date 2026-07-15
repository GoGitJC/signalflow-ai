# Retell AI integration

## Role

Retell provides the voice agent. SignalFlow ingests **call-started** and **call-ended** webhooks to persist callers, calls, transcripts, and optional appointments.

## Endpoints

| Method | Path |
|--------|------|
| `POST` | `/api/webhooks/retell/call-started` |
| `POST` | `/api/webhooks/retell/call-ended` |

## Authentication

Header: `X-Retell-Signature`

- If `SIGNALFLOW_RETELL_WEBHOOK_SECRET` is empty → signature check skipped (local/dev).
- If set → HMAC-SHA256 of raw body required (`sha256=` prefix accepted).

## Call-started

Creates a `calls` row when the business exists. Idempotent via `webhook_events`.

Payload highlights: `business_id`, `retell_call_id`, `started_at`, optional `caller_phone`, `direction`, `event_id`.

## Call-ended

Runs `process_completed_call`:

1. Upsert caller by `(business_id, phone)`
2. Upsert/update call with transcript, summary, intent, urgency, outcome
3. Create/update appointment when appointment payload present
4. Commit transactionally

## Local simulation

```bash
BUSINESS_ID=<uuid> ./scripts/simulate_call.sh
```

Posts a sample call-ended payload with an appointment.

## Production checklist

- [ ] Configure webhook secret
- [ ] Register public HTTPS URLs in Retell
- [ ] Map Retell agent IDs to `voice_agents` rows
- [ ] Confirm idempotency with Retell retries
