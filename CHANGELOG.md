# Changelog

All notable changes to ForgeLinq are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) where practical.

## [Unreleased]

### Changed

- Product branding (user-facing): SignalFlow AI → **ForgeLinq** (repo/package/env names unchanged).
- Retell agent listing uses `POST /v2/list-agents` with voice filter + pagination (`items` / `has_more` / `pagination_key`).

### Added

- Booking path structured logs (masked email/phone), placeholder email rejection, Cal.com attendee `language`, stronger booking idempotency after provider success.
- Retell tool configuration guide: `docs/integrations/retell-tools.md`.
- Production deployment pack: `render.yaml`, `frontend/vercel.json`, `.env.production.example`, Cloudflare/Render/Vercel runbooks, `LAUNCH_CHECKLIST.md`, disaster-recovery guide.
- Multi-origin `CORS_ORIGINS`, optional `TRUSTED_HOSTS`, `APP_ENV` alias, Render `postgresql://` → `psycopg` URL normalization, `$PORT`-aware backend image.
- Closed-beta launch pack: HVAC demo tenant (`Summit HVAC Pros`), onboarding welcome + test-call checklist, Final Acceptance page (`/readiness`), CSV exports, searchable audit log.
- Marketing polish: brand logo, favicon, loading screen, 404 page, empty-state illustrations, Help deep links.
- Release notes: `docs/RELEASE_NOTES_v1.0_BETA.md`.
- Phase 5 production readiness: structured JSON logging + request IDs, unified API error schema, rate limits on auth/webhooks, `/health` `/live` `/ready` `/metrics`, production config fail-fast, demo seed CLI, first-run onboarding wizard.
- Frontend production Docker image (nginx + CSP) alongside Vite development target.
- Ops docs: `docs/operations.md`, `docs/monitoring.md`, `docs/onboarding.md`, `docs/demo-data.md`; expanded deployment (Render/Railway/DO/AWS).
- Cookie-based auth UX: HttpOnly `sf_access`/`sf_refresh` sessions, login/register/forgot/reset/verify/invite flows, `AuthProvider`, protected routes, Settings users/invitations.
- Migration `0007_auth_sessions` — email verification timestamp, password reset tokens, invitations.
- Auth guide: `docs/auth.md`.
- Phase 3 customer experience: CRM callers API (notes/tags/status), analytics summary, voice-agent config API, KB bulk import + version history, audit event list, call sentiment.
- Migration `0006_crm_experience` for callers CRM fields, voice agent config, KB versions, call sentiment.
- Dashboard product guide: `docs/dashboard.md`.
- TanStack Query data layer on the React dashboard.
- Phase 2 auth slice: `POST /api/auth/register|login|refresh`, `GET /api/auth/me`, JWT access/refresh tokens, `users.password_hash`, `refresh_tokens` migration `0004_auth_tokens`.
- Auth audit foundation: `auth_audit_events` migration `0005_auth_audit_events` for register/login/refresh outcomes.
- Integration admin routes accept Bearer JWT (owner/admin) with legacy `X-Owner-Token` fallback.
- Tenant CRUD (calls, appointments, KB, business read/update) requires JWT membership or legacy owner headers; `POST /api/businesses` requires bootstrap owner token.
- Final Production Acceptance Checklist in `docs/production-readiness.md` (valid-customer live booking, SMS, duplicates, cancellation).
- Live acceptance report: `docs/integrations/live-acceptance-2026-07-16.md` — Phase B verified; Phase C Cal.com `400` classified as invalid test email input (not an architecture blocker).
- Retell custom-function envelope unwrap (`{call, name, args}`) for live tool POSTs.
- `ALLOW_LIVE_BOOKING` pytest coverage and cross-tenant denial on Cal.com owner routes.
- Live-ready Retell ↔ Cal.com flow: voice-friendly tool schemas, booking confirmation gate, call linkage.
- `ALLOW_LIVE_BOOKING` guard (default false) to prevent accidental paid Cal.com bookings.
- `CALCOM_EVENT_TYPES_API_VERSION` (default `2024-06-14`) for event-type endpoints.
- Migration `0003_voice_agent_unique` — one Retell agent maps to exactly one business.
- CLI `python -m app.cli.sync_live_integrations` to persist verified IDs onto a business.
- Scripts: `scripts/prepare_integration_keys.py`, `scripts/verify_integrations.sh`.
- Expanded mocked tests in `test_live_flow.py` (mapping, slots, booking, webhooks, tenants).

### Changed

- CI builds frontend `production` and `development` Docker targets.
- Dashboard authentication no longer uses `localStorage` JWTs or `VITE_OWNER_API_TOKEN`; sessions use HttpOnly cookies with automatic refresh.
- Dashboard pages upgraded for daily CRM use: Customers, Calls (transcript/timeline/AI actions), Appointments filters, Analytics executive metrics, Voice Agent API config, Knowledge versions/bulk, Settings audit log.
- Documentation treats Retell/Cal.com availability/webhooks/dashboard as engineering-complete; final booking validation is release checklist only.
- `POST /api/integrations/calcom/availability` and `/book` require owner auth (`X-Owner-Token`, `X-Business-Id`) and reject mismatched body `business_id`.
- `INTEGRATION_MODE` replaces mock-only 501 behavior; mock adapters preserved for tests.
- Retell webhooks resolve `business_id` from `voice_agents.retell_agent_id` when using official payload format.
- `.env.example` documents Retell, Cal.com, owner token, and public API URL variables.
- Retell tool responses return spoken summaries and `option_id` values for agent booking.
- Connection tests persist `last_test_*` fields for both mock and live modes.
- Integration settings API: Retell/Cal.com status, credential upsert, connection tests.
- Retell tool endpoints: `check_availability`, `book_appointment` (agent → business mapping).
- Unified Retell webhook route `/api/webhooks/retell` with official signature verification in live mode.
- Cal.com v2 slots/booking client, transactional booking, duplicate protection, webhook status sync.
- Encrypted per-business credentials, integration audit events, migration `0002_integrations`.
- CLI: `python -m app.cli.resolve_retell_agent`.
- Frontend Settings integration cards (masked IDs, test connection, password inputs).
- Tests: Retell/Cal.com provider mocks, signatures, cross-tenant denial, E2E mocked flow.

### Security

- Live Retell webhooks require `X-Retell-Signature` verified with API key.
- Integration admin and Cal.com scheduling routes require `X-Owner-Token`; API keys never returned to frontend.

### Added (prior)

- Premium dashboard redesign: design tokens, shadcn-style component library, dark mode, full sidebar IA, charts, skeletons, empty/error states.
- `docs/ui.md` for design philosophy, palette, components, typography, responsive behavior, dark mode, and motion.
- Compose `backend-test` service and Dockerfile `development` target with `[dev]` extras (`pytest`, `ruff`, `mypy`).
- README verification suite using `docker compose run --rm backend-test …`.
- `httpx2` in backend `[dev]` extras for Starlette `TestClient`.

### Changed

- Frontend layout: `components/`, `hooks/`, `lib/`, `pages/`, `types/` with shared API client.
- Backend Dockerfile is multi-stage: `development` (tools) vs `production` (runtime only).
- `mypy` config excludes `tests/` and `alembic/` so `mypy .` succeeds in Compose.

### Fixed

- Quality tools missing from runtime image PATH — available via `backend-test` only.
- Pytest `StarletteDeprecationWarning` for deprecated `httpx` TestClient usage.

## [0.1.2] - 2026-07-14

### Added

- `scripts/dev-up.sh` for one-command local stack start (optional `--reset`).
- Compose backend healthcheck; frontend waits for healthy backend.
- Expanded `.env.example` comments for Twelve-Factor local setup.

### Changed

- Backend Dockerfile installs the package with `app/` and `alembic/` present so wheels include application code.
- ORM enums use named types with `create_type=False` so models never emit `CREATE TYPE` (Alembic owns enum DDL).
- Timezone-aware `utcnow()` helpers replace deprecated `datetime.utcnow`.

### Fixed

- Foundation verification: clean `docker compose down -v` + `up --build` migrates once, backend stays healthy, `/health` returns 200.

## [0.1.1] - 2026-07-14

### Added

- Phase 11 project governance: polished README, `docs/` suite, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, LICENSE, issue/PR templates, Dependabot, and GitHub Actions CI.
- Backend mypy configuration for CI typing checks.

### Fixed

- Alembic `0001_initial` migration no longer double-creates PostgreSQL enums (`userrole`, `integrationprovider`); uses `postgresql.ENUM(..., create_type=False)` after explicit type create. Downgrade drops tables before enums.

## [0.1.0] - 2026-07-14

### Added

- Multi-tenant FastAPI backend with business, knowledge-base, calls, appointments, integrations, and webhook APIs.
- PostgreSQL schema via Alembic initial migration.
- Mock Cal.com and Twilio adapters; Retell call-started / call-ended webhooks with idempotency.
- React + Vite dashboard (overview, calls, appointments, knowledge base, settings shell).
- Docker Compose stack and `scripts/simulate_call.sh`.
- Backend pytest suite for health, tenant flows, mocks, and Retell webhooks.
