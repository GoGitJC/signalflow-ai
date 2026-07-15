# Twilio integration

## Role

Twilio will send SMS (e.g. post-call summaries). This phase exposes a mock send path only.

## Endpoint

| Method | Path |
|--------|------|
| `POST` | `/api/integrations/twilio/send-summary` |

Body: `business_id`, `to`, `message`.

Response (mock): `message_id`, `status` (`queued`), `mocked: true`.

## Mock vs live

- `SIGNALFLOW_MOCK_EXTERNAL_SERVICES=true` → `MockTwilioClient`
- `false` → **HTTP 501** (`Live provider clients are not configured in this phase`)

Env vars `SIGNALFLOW_TWILIO_ACCOUNT_SID` and `SIGNALFLOW_TWILIO_AUTH_TOKEN` are reserved for the live client (Phase 3).

## Production checklist

- [ ] Store account credentials encrypted per business (`integrations` table)
- [ ] Validate webhook signatures for delivery status callbacks
- [ ] Persist outbound message IDs and delivery state
- [ ] Add retries / DLQ for failures
