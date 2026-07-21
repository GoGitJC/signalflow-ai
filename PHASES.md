# ForgeLinq Delivery Phases

Each phase must finish with a runnable application, passing tests, updated migrations, and documented local verification.

## Phase 1 — Foundation and simulated completed-call flow

- Monorepo, Docker Compose, environment configuration
- FastAPI application and PostgreSQL persistence
- Core multi-tenant models and initial Alembic migration
- Business and knowledge-base CRUD
- Call, caller, appointment persistence
- Idempotent simulated Retell call-ended webhook
- Mock Cal.com and Twilio adapters
- Dashboard overview, calls, appointments, knowledge base, settings shell
- Backend tests and frontend production build

## Phase 2 — Authentication and tenant authorization

- Passwordless or email/password owner authentication
- JWT access and refresh token lifecycle
- User memberships and role-based authorization
- Resolve tenant from authenticated membership instead of client-supplied trust
- Tenant-isolation integration tests
- Audit event foundation

## Phase 3 — Provider integration architecture

- Provider interfaces and dependency-injected production adapters
- Encrypted integration credentials with key rotation support
- Retell signature validation and normalized webhook contracts
- Twilio Messaging API integration and delivery-state persistence
- Cal.com availability and booking integration
- Provider timeout, retry, and circuit-breaker policies

## Phase 4 — Receptionist orchestration

- Business-hours and service-area rules
- Knowledge-base retrieval and prompt assembly
- Lead qualification schema
- Urgency and transfer decision rules
- Appointment confirmation workflow
- Unsupported-call fallback behavior

## Phase 5 — Production dashboard

- Authenticated application shell (login UI remaining)
- CRM customers, call intelligence, appointments filters, analytics ranges (shipped in Phase 3 CX)
- Paginated/filterable calls and appointments
- Transcript and recording views
- Knowledge-base editing forms (bulk + versions)
- Business and integration settings + audit log
- Loading, empty, validation, and error states

## Phase 6 — Asynchronous processing and observability

- Background jobs for SMS, retries, and post-call workflows
- Structured logging with PII redaction
- Metrics, tracing, health/readiness endpoints
- Dead-letter handling and webhook replay tooling
- Rate limiting and abuse controls

## Phase 7 — Deployment and operations

- Production Docker images
- CI pipeline for lint, tests, migrations, and builds
- Render/Railway/Fly.io deployment guides
- AWS and DigitalOcean reference architectures
- Managed PostgreSQL, backups, TLS, secrets, and rollback procedures
- Load tests and capacity targets
