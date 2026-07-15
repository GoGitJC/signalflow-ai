# Changelog

All notable changes to SignalFlow AI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) where practical.

## [Unreleased]

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
