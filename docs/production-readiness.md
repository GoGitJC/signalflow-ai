# Production readiness

Verideum is **not production-ready for untrusted multi-tenant traffic** until authentication and the Final Production Acceptance Checklist are complete. Use this document before accepting real callers.

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
- [ ] Appointment appears in the **Verideum** dashboard under the correct business
- [ ] Cal.com booking **UID** stored locally as `appointments.cal_event_id`
- [ ] Booking **confirmation SMS** delivered (Twilio live path or approved substitute)
- [ ] **Duplicate booking protection** verified (second identical book does not create a second Cal.com event)
- [ ] Booking **cancellation** verified (Cal.com cancel syncs or is reconciled in Verideum)

Until this checklist is signed off, leave `ALLOW_LIVE_BOOKING=false`.

## Demo / pre-merge live checks (already exercised)

- [x] `ALLOW_LIVE_BOOKING=false` in runtime after tests
- [x] Public `/health` 200 through tunnel URL
- [x] No-booking live call: availability 200, book 403, call persisted
- [x] Gate restored to false after booking attempts
- [x] Results recorded in `docs/integrations/live-acceptance-*.md`
- [ ] Remember ngrok free URLs expire/change on restart (ongoing ops)

## Deployment verification (closed beta)

Before inviting a real customer:

1. **Env:** `JWT_SECRET`, `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY`, `SIGNALFLOW_FRONTEND_ORIGIN`, `AUTH_COOKIE_SECURE=true` (prod), `ALLOW_LIVE_BOOKING=false`, `LOG_JSON=true`, `RATE_LIMIT_ENABLED=true`
2. **HTTPS:** Terminate TLS at the load balancer / CDN; API and dashboard on HTTPS (except local Compose)
3. **Cookies:** Secure + HttpOnly; CORS origin exact match
4. **Build:** `docker build --target production ./frontend` and backend production image; CI green
5. **Probes:** `/live` + `/ready` wired; open `/readiness` in the dashboard for a live score

See [deployment.md](deployment.md) and [RELEASE_NOTES_v1.0_BETA.md](RELEASE_NOTES_v1.0_BETA.md).

## Must-have before go-live

- [x] Authentication and membership authorization (Phase 2 / cookie UX)
- [ ] Final Production Acceptance Checklist (above)
- [x] Webhook secrets supported; mandatory in production live mode (startup validation)
- [x] Encrypted credential storage with managed key (fail-fast in production)
- [ ] TLS everywhere (dashboard, API, DB preference) — platform-dependent
- [ ] Managed Postgres backups + tested restore (procedure documented)
- [x] Structured logging with PII redaction helpers + request IDs
- [x] Health **and** readiness probes (`/health`, `/live`, `/ready`)
- [x] Rate limiting on auth/webhook endpoints
- [x] Metrics exposition (`/metrics`)
- [x] Incident/ops runbook ([operations.md](operations.md))
- [ ] On-call ownership assigned for first customer

## Recommended GitHub branch protection (`main`)

1. Require pull request before merging.
2. Require status checks to pass: `Backend quality`, `Frontend quality`, `Docker image builds`.
3. Require branches to be up to date before merging.
4. Restrict force pushes and deletions on `main`.

## Required CI checks before merge

| Job | Verifies |
|-----|----------|
| Backend quality | `ruff format --check`, `ruff check`, `mypy`, `pytest` |
| Frontend quality | `tsc --noEmit`, `npm run build` |
| Docker image builds | backend + frontend `production`/`development` targets |

## Operational maturity (later)

- Redis-backed multi-instance rate limits
- Distributed tracing (OpenTelemetry)
- Dead-letter webhook replay
- Capacity / load testing
- Blue/green or canary deploys
