# Retell agent configuration for ForgeLinq custom tools

## Tools (source of truth)

Do **not** enable Retell-native Cal.com booking tools. Use ForgeLinq custom functions:

| Tool | Method | Path |
|------|--------|------|
| `check_availability` | POST | `{APP_PUBLIC_API_URL}/api/retell/tools/check_availability` |
| `book_appointment` | POST | `{APP_PUBLIC_API_URL}/api/retell/tools/book_appointment` |

## Payload mode

Prefer Retell **custom function envelope**:

```json
{ "name": "book_appointment", "call": { "call_id": "...", "agent_id": "..." }, "args": { ... } }
```

ForgeLinq also accepts **args-only** flat bodies when that Retell setting is enabled.

Malformed envelopes (`call` without `args`) return HTTP **422**.

## `check_availability` args

| Field | Required | Notes |
|-------|----------|-------|
| `start` | yes | Window start (ISO-8601) |
| `end` | yes | Window end |
| `timezone` | no | Default `America/Chicago` |
| `max_options` | no | 1–10, default 5 |
| `retell_agent_id` | via call/args | Resolved to tenant |

## `book_appointment` args

| Field | Required | Notes |
|-------|----------|-------|
| `start` | yes | UTC or offset datetime |
| `option_id` | recommended | From availability (`slot_<epoch>`) — preferred over free-form start |
| `name` | yes | Real caller full name |
| `email` | yes | Real deliverable email — **not** `@example.com` |
| `phone` | recommended | E.164 when SMS reminders are enabled on the Cal.com event |
| `service` | yes | Service label |
| `timezone` | no | Default `America/Chicago` |
| `caller_confirmed` | yes | Must be `true` after explicit verbal confirmation |
| `retell_call_id` | recommended | Links appointment to call |

## Agent prompt — BOOKING RULES

```text
BOOKING RULES
- Collect the caller’s real full name.
- Collect and confirm the caller’s real email address.
- Collect and confirm the caller’s phone number.
- Never invent or substitute an email address.
- Never use mail@example.com or another placeholder.
- Check availability before booking.
- Read the selected date and time back to the caller.
- Confirm the caller wants that exact slot.
- Only call book_appointment after explicit confirmation (caller_confirmed=true).
- If booking fails, do not claim the appointment was booked.
- If booking succeeds, tell the caller the confirmed date and time.
- Do not call book_appointment more than once for the same confirmed slot.
```

## Live booking gate

Even in `INTEGRATION_MODE=live`, Cal.com bookings require `ALLOW_LIVE_BOOKING=true`.
Keep it `false` except during an approved controlled test.
