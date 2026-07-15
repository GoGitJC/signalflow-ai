# Cal.com integration

## Role

Cal.com provides availability and booking. SignalFlow also accepts Cal.com webhooks for future sync.

## REST (mock)

| Method | Path | Behavior |
|--------|------|----------|
| `POST` | `/api/integrations/calcom/availability` | Up to 8 hourly slots between `start` and `end` |
| `POST` | `/api/integrations/calcom/book` | Returns `mock-cal-{uuid}`, 30-minute window, `status: booked` |

Responses include `mocked: true` when mocks are enabled. Live mode returns **501**.

## Webhook

| Method | Path | Header |
|--------|------|--------|
| `POST` | `/api/webhooks/calcom` | `X-Cal-Signature` |

Currently acknowledges and claims idempotency only — does not mutate appointments yet.

Secret: `SIGNALFLOW_CALCOM_WEBHOOK_SECRET`.

## Appointment persistence from voice

Completed Retell calls may include an `appointment` object; that path creates rows in `appointments` with optional `cal_event_id`, independent of the Cal.com REST mock.

## Production checklist

- [ ] Live availability/booking HTTP client
- [ ] Per-tenant Cal.com credentials in `integrations`
- [ ] Webhook handlers that update appointment status
- [ ] Conflict / cancellation handling
