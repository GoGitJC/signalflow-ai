# Production readiness

SignalFlow AI is **not production-ready for untrusted multi-tenant traffic** until authentication and live provider hardening land. Use this checklist before accepting real callers.

## Live integration acceptance (pre-merge)

Before treating Retell/Cal.com as demo-ready:

- [ ] `ALLOW_LIVE_BOOKING=false` in runtime
- [ ] Public `/health` 200 through current tunnel URL
- [ ] No-booking live call: availability 200, book 403, call persisted
- [ ] Controlled booking only with written operator approval
- [ ] Gate restored to false after any booking attempt
- [ ] Record results in `docs/integrations/live-acceptance-*.md`
- [ ] Remember ngrok free URLs expire/change on restart

Latest run: [docs/integrations/live-acceptance-2026-07-16.md](integrations/live-acceptance-2026-07-16.md) — Phase B passed; Phase C booking stopped after Cal.com `400`.

## Must-have before go-live

- [ ] Authentication and membership authorization (Phase 2)
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
