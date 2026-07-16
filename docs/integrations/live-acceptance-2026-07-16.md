# Live acceptance report — Retell + Cal.com

Date: 2026-07-16  
Branch: `feature/live-retell-calcom-flow`  
Business ID: `d9afc92e-807b-45ad-9b43-2482edf8d987`  
Retell agent: `Universal_DEMO` (`agent_87484b6b91fd9fbdc687090d5d`)  
Cal.com event type: `60-min` (`6283508`)

## Summary

| Phase | Result |
|-------|--------|
| A — Pre-flight | **PASS** |
| B — No-booking live call | **PASS** |
| C — Controlled booking | **STOPPED / FAIL** (Cal.com `400` on book; API retry declined) |
| Gate final | `ALLOW_LIVE_BOOKING=false` |

## Phase B — no-booking call

| Item | Value |
|------|--------|
| Retell call ID | `call_0b102beae52a15dfe7c2ccf6561` |
| Internal call ID | `23e766f5-180d-4bf1-8045-e5bce5e05385` |
| `check_availability` | HTTP **200**, real slots returned |
| `book_appointment` | HTTP **403** (gate blocked; `caller_confirmed=true`) |
| New appointments | **0** (count unchanged) |
| Webhooks | `call_started` / `call_ended` / `call_analyzed` accepted |
| Dashboard | Call visible; transcript + summary stored |
| `appointment_booked` | `false` |
| Notes | `intent` empty; caller row had phone but name/email not always populated |

## Phase C — controlled booking

| Item | Value |
|------|--------|
| Retell call ID | `call_63ea25c9cab7198905c4eb63d85` |
| `check_availability` | HTTP **200** |
| `book_appointment` (Retell) | HTTP **400** · Cal.com booking failed |
| API booking (approved) | HTTP **400** · same generic failure |
| Local appointment created | **No** |
| Probe booking | Accidental Cal.com UID `1ARjkDcqs8XzegKC3cTfns` created during diagnosis, then **cancelled** |
| Operator decision | **stop** — no further booking retries |

Likely causes under investigation: attendee phone validation and/or opaque Cal.com error mapping (SignalFlow returns a generic 400). Slot remained available after failures.

## Gate

- Enabled only during controlled attempts.
- Restored to **`ALLOW_LIVE_BOOKING=false`** after each attempt and at stop.
- Follow-up book with gate off returns HTTP **403**.

## Dashboard verification

- Calls list includes Phase B and Phase C calls.
- Appointments list still shows only the earlier demo booking (`vaF1RKh9DxzkY4bqfEL9Xt…`), not a Phase C booking.

## Known limitations

1. Cal.com booking errors are not surfaced to operators beyond a generic message.
2. Retell STT can alter email domains (e.g. `@gwelin.com` vs `@gwellen.com`).
3. `intent` may be empty on analyzed calls.
4. Caller name/email may be missing on the caller row even when present in tool args.
5. Phone on `book_appointment` may contribute to Cal.com `400` (unconfirmed; retry-without-phone was not approved).

## ngrok URL volatility

Public URL used during acceptance:

`https://breezy-crane-wrongness.ngrok-free.dev`

ngrok free URLs change when the tunnel restarts. After any restart, update:

- `APP_PUBLIC_API_URL`
- `RETELL_WEBHOOK_BASE_URL`
- Retell agent webhook URL
- Retell custom function URLs

Then recreate the backend and re-check public `/health`.
