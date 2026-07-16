# SignalFlow AI v1.0 Beta — Release Notes

**Release:** SignalFlow AI v1.0 Beta  
**Audience:** Closed-beta operators and first design partners  
**Date:** 2026-07-16

## What’s included

SignalFlow AI is an AI receptionist OS for service businesses: inbound voice, appointment booking, CRM, and operator dashboard.

This beta ships a production-oriented foundation suitable for a **closed pilot** with `ALLOW_LIVE_BOOKING=false` until Final Acceptance is signed off.

### Product
- Multi-tenant FastAPI backend + React dashboard
- Cookie-based auth (HttpOnly sessions)
- Calls, appointments, customers, knowledge base, voice agent, analytics
- Retell + Cal.com integrations (mock or live)
- First-run onboarding wizard (welcome → providers → KB → test-call checklist)
- Final Acceptance Checklist page (`/readiness`)
- HVAC demo tenant seed for realistic demos

### Operations
- `/health`, `/live`, `/ready`, `/metrics`
- Structured JSON logging + request IDs
- Auth/webhook rate limiting
- Production config fail-fast
- CSV exports (customers, appointments, calls)
- Searchable audit log
- CI: lint, typecheck, tests, Docker image builds

### Polish
- Brand mark + favicon
- Loading screen, 404 page, empty-state illustrations
- Help links throughout the dashboard

## Known limitations

- Live Twilio SMS is a placeholder until Final Acceptance
- Email verify/reset/invite delivery is stubbed in beta
- Keep `ALLOW_LIVE_BOOKING=false` until a valid-customer booking is verified
- In-process rate limits (not Redis) for single-instance deploys

## Getting started (beta)

1. Deploy or run Compose — see `docs/deployment.md`
2. Seed demo: `python -m app.cli.seed_demo` — see `docs/demo-data.md`
3. Complete `/onboarding`
4. Review `/readiness` before inviting the first real customer

## Upgrade / rollback

Follow `docs/operations.md` for backups, restore, and migration rollback.

## Support

Internal closed-beta channel + repository docs under `docs/`.
