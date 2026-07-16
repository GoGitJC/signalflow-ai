# Production readiness

SignalFlow AI is **not production-ready for untrusted multi-tenant traffic** until authentication and the Final Production Acceptance Checklist are complete. Use this document before accepting real callers.

## Integration status (engineering)

| Area | Status |
|------|--------|
| Retell live tools + webhooks | **Complete** (verified in live acceptance) |
| Cal.com availability | **Complete** (verified live) |
| Cal.com booking path | **Implemented**; final validation with valid customer data is a **release checklist** item |
| Dashboard call/appointment persistence | **Complete** |
| `ALLOW_LIVE_BOOKING` | Keep **`false`** until Final Production Acceptance |

Live acceptance notes: [integrations/live-acceptance-2026-07-16.md](integrations/live-acceptance-2026-07-16.md).

A Cal.com HTTP `400` during controlled testing was caused by **invalid attendee email input**, not by a missing booking architecture.

## Final Production Acceptance Checklist

Complete before enabling live booking in a shared/production environment:

- [ ] Successful live booking with **valid** attendee name, email, and phone
- [ ] Booking appears in **Cal.com** for the mapped event type
- [ ] Appointment appears in the **SignalFlow** dashboard under the correct business
- [ ] Cal.com booking **UID** stored locally as `appointments.cal_event_id`
- [ ] Booking **confirmation SMS** delivered (Twilio live path or approved substitute)
- [ ] **Duplicate booking protection** verified (second identical book does not create a second Cal.com event)
- [ ] Booking **cancellation** verified (Cal.com cancel syncs or is reconciled in SignalFlow)

Until this checklist is signed off, leave `ALLOW_LIVE_BOOKING=false`.

## Demo / pre-merge live checks (already exercised)

- [x] `ALLOW_LIVE_BOOKING=false` in runtime after tests
- [x] Public `/health` 200 through tunnel URL
- [x] No-booking live call: availability 200, book 403, call persisted
- [x] Gate restored to false after booking attempts
- [x] Results recorded in `docs/integrations/live-acceptance-*.md`
- [ ] Remember ngrok free URLs expire/change on restart (ongoing ops)

## Must-have before go-live

- [ ] Authentication and membership authorization (Phase 2)
- [ ] Final Production Acceptance Checklist (above)
- [ ] Webhook secrets mandatory in production
- [ ] Live provider clients with timeouts, retries, and error budgets
- [ ] Encrypted credential storage with managed key
- [ ] TLS everywhere (dashboard, API, DB preference)
- [ ] Managed Postgres backups + tested restore
- [ ] Structured logging with PII redaction
- [ ] Health **and** readiness probes (DB connectivity)
- [ ] Rate limiting on public endpoints
- [ ] Incident runbook and on-call ownership

## Recommended GitHub branch protection (`main`)

1. Require pull request before merging.
2. Require status checks to pass:
   - `Backend quality`
   - `Frontend quality`
   - `Docker image builds`
3. Require branches to be up to date before merging.
4. Restrict force pushes and deletions on `main`.
5. Optionally require 1 approving review.

## Required CI checks before merge

Documented in `.github/workflows/ci.yml`:

| Job | Verifies |
|-----|----------|
| Backend quality | `ruff format --check`, `ruff check`, `mypy`, `pytest` |
| Frontend quality | `tsc --noEmit`, `npm run build` |
| Docker image builds | `docker build` for backend and frontend |

## Operational maturity (Phase 6–7)

- Async SMS / post-call jobs
- Metrics and tracing
- Dead-letter webhook replay
- Capacity / load testing
- Blue/green or canary deploys
