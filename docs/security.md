# Security

## Current posture (MVP foundation)

| Area | Status |
|------|--------|
| Authentication | Not implemented |
| Authorization | Role enum exists; not enforced on routes |
| Tenant isolation | Enforced via `business_id` filters and FK checks |
| Webhook integrity | Optional HMAC when secrets configured |
| Secrets in git | Blocked via `.gitignore` and review process |
| Credential storage | `encrypted_credentials` column reserved; key env var reserved |

## Threats acknowledged

1. **Client-supplied `business_id`** — attackers who know a UUID can act as that tenant until auth lands.
2. **Unsigned webhooks in development** — acceptable only with empty secrets; production must set secrets.
3. **Open CORS origin misconfiguration** — `SIGNALFLOW_FRONTEND_ORIGIN` must match the real dashboard URL.

## Secrets handling

- Never commit `.env`, dumps, private keys, or provider tokens.
- Report exposed secrets per [SECURITY.md](../SECURITY.md).
- Rotate keys after any accidental exposure.

## Recommended next controls (Phase 2+)

- JWT/session auth and membership-scoped `business_id`
- RBAC using `UserRole`
- Mandatory webhook signatures in non-dev environments
- PII redaction in logs
- Rate limiting on public webhook and auth endpoints

## Branch protection / CI

Required checks and rules are documented in [CONTRIBUTING.md](../CONTRIBUTING.md) and [production-readiness.md](production-readiness.md).
