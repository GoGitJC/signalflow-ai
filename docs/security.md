# Security

## Integration posture

| Area | Status |
|------|--------|
| Tenant isolation | `business_id` on all repository queries; Retell tools resolve business via agent mapping |
| Provider credentials | Encrypted at rest (Fernet) in `integrations.encrypted_credentials` |
| API responses | Secrets never returned; IDs masked |
| Webhook integrity | Live Retell: official `X-Retell-Signature` + API key; Cal.com: optional HMAC |
| Integration admin | Bearer JWT (owner/admin) or legacy `X-Owner-Token` + `X-Business-Id` |
| Tenant dashboard APIs | Bearer JWT (any role) or legacy owner headers; path/body tenant must match |
| Auth audit | `auth_audit_events` for register/login/refresh |
| Logging | Do not log API keys, webhook bodies, transcripts, or phone numbers |

## Threats acknowledged

1. **Client-supplied `business_id` on open routes** — Retell tool endpoints ignore caller-supplied business IDs.
2. **Unsigned webhooks in mock mode** — acceptable only with `INTEGRATION_MODE=mock` and empty secrets.
3. **Owner token in frontend env** — `VITE_OWNER_API_TOKEN` is for local admin only; use proper auth in production.

## Credential rotation

1. Generate new provider API key in Retell or Cal.com dashboard
2. Update `.env` or PUT integration settings with `confirm_replace: true`
3. Revoke old key at provider
4. Re-run connection test and audit `integration_audit_events`

## Webhook signature errors

See [integrations/retell.md](integrations/retell.md) — common causes:

- Re-serialized JSON instead of raw body
- Wrong API key (must have webhook badge)
- Clock skew beyond 5 minutes

## Secrets handling

- Never commit `.env`, dumps, or provider tokens
- Report exposure per [SECURITY.md](../SECURITY.md)
- Run secret scan before commits

## Recommended next controls

- JWT/session auth replacing owner token header (in progress: JWT + legacy owner-token fallback on tenant and integration routes)
- Frontend login UI replacing `VITE_OWNER_API_TOKEN` for production dashboards
- Multi-business memberships table beyond single `users.business_id`
- Mandatory webhook signatures in all non-dev environments
- PII redaction middleware in structured logs
- Rate limiting on webhooks and tool endpoints
