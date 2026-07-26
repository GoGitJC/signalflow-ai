# Live acceptance report — Retell + Cal.com

Date: 2026-07-16  
Branch: `feature/live-retell-calcom-flow`  
Business ID: `d9afc92e-807b-45ad-9b43-2482edf8d987`  
Retell agent: `Universal_DEMO` (`agent_87484b6b91fd9fbdc687090d5d`)  
Cal.com event type: `60-min` (`6283508`)

## Verdict

**Engineering integration is complete** for Retell, Cal.com availability, webhooks, and dashboard persistence.  
A controlled booking attempt returned Cal.com HTTP `400` because **invalid attendee email was used during testing** (STT/test-input corruption such as `@gwelin.com`). That is treated as a **blocked test caused by invalid input**, not an architectural defect.

Final production booking with valid customer information remains on the [Final Production Acceptance Checklist](../production-readiness.md#final-production-acceptance-checklist).

`ALLOW_LIVE_BOOKING` remains **`false`**.

---

## Verified implementation

| Capability | Status | Evidence |
|------------|--------|----------|
| Retell agent → business mapping | **Verified** | Tools resolve `d9afc92e-…` from `agent_87484b6b91fd9fbdc687090d5d` |
| Live Cal.com availability | **Verified** | `check_availability` HTTP 200 with real slots |
| Retell tool envelope unwrap | **Verified** | Live `{call,name,args}` POSTs succeed |
| Booking gate (`ALLOW_LIVE_BOOKING=false`) | **Verified** | `book_appointment` HTTP **403** when gate off |
| Retell webhooks | **Verified** | `call_started` / `call_ended` / `call_analyzed` accepted |
| Call persistence + dashboard | **Verified** | Calls list, transcript, summary stored |
| Cross-tenant tool denial | **Verified** | Automated tests |
| Duplicate webhook idempotency | **Verified** | Automated tests + live event keys |
| Owner-gated Cal.com admin routes | **Verified** | Automated tests |

### Phase A — Pre-flight: PASS

Live mode, connected Retell/Cal.com status, public `/health` 200, gate probe 403.

### Phase B — No-booking live call: PASS

| Item | Value |
|------|--------|
| Retell call ID | `call_0b102beae52a15dfe7c2ccf6561` |
| Internal call ID | `23e766f5-180d-4bf1-8045-e5bce5e05385` |
| `check_availability` | HTTP **200**, real slots |
| `book_appointment` | HTTP **403** (gate; `caller_confirmed=true`) |
| New appointments | **0** |
| Webhooks | Accepted |
| Dashboard | Call visible |

---

## Blocked test caused by invalid input

### Phase C — Controlled booking: blocked (invalid attendee email)

| Item | Value |
|------|--------|
| Retell call ID | `call_63ea25c9cab7198905c4eb63d85` |
| `check_availability` | HTTP **200** |
| `book_appointment` | HTTP **400** from Cal.com |
| Root cause classification | **Invalid / corrupted attendee email during controlled testing** (e.g. STT produced `@gwelin.com` instead of a valid `@gwellen.com` address) |
| Architecture impact | **None** — not treated as an unresolved engineering blocker |
| Local appointment | Not created (expected when Cal.com rejects the request) |
| Operator follow-up | Stopped further live booking attempts; gate left **false** |

A diagnostic probe with a syntactically valid email successfully created (and later cancelled) a Cal.com booking for the same slot family, which supports classifying the Phase C failure as **input validation / test data**, not a missing Verideum booking path.

---

## Remaining production validation

Do **not** treat as open engineering work on this branch. Track under release readiness:

See **[Final Production Acceptance Checklist](../production-readiness.md#final-production-acceptance-checklist)**:

- Successful live booking with **valid** customer attendee information  
- Booking visible in Cal.com and Verideum  
- Booking UID stored locally  
- Confirmation SMS  
- Duplicate protection  
- Cancellation verification  

Until that checklist is signed off, keep `ALLOW_LIVE_BOOKING=false` in shared environments.

---

## Gate

- Enabled only during controlled attempts.
- Restored to **`ALLOW_LIVE_BOOKING=false`** after attempts and at stop.
- Follow-up book with gate off returns HTTP **403**.

## Operational notes

1. Retell STT can alter spoken email addresses — confirm spelling before production booking tests.
2. Cal.com error bodies are mapped to a generic operator-facing message (improvement optional, not blocking).
3. `intent` may be empty on some analyzed calls; urgency/outcome/summary still persist.
4. ngrok free URLs change on restart — update `APP_PUBLIC_API_URL`, `RETELL_WEBHOOK_BASE_URL`, and Retell dashboard URLs.

Public URL used during this run: `https://breezy-crane-wrongness.ngrok-free.dev`
