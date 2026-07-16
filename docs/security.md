# Security

## Integration posture

| Area | Status |
|------|--------|
| Tenant isolation | `business_id` on all repository queries; Retell tools resolve business via agent mapping |
| Provider credentials | Encrypted at rest (Fernet) in `integrations.encrypted_credentials` |
| API responses | Secrets never returned; IDs masked |
| Webhook integrity | Live Retell: official `X-Retell-Signature` + API key; Cal.com: optional HMAC |
| Integration admin | Cookie/JWT session (owner/admin) or legacy `X-Owner-Token` + `X-Business-Id` |
| Tenant dashboard APIs | Cookie/JWT session (any role) or legacy owner headers |
| Auth audit | `auth_audit_events` for register/login/refresh/logout/reset/invite |
| Dashboard tokens | HttpOnly cookies only — never `localStorage` |
| Logging | Structured JSON + request IDs; redact secrets/PII (`app.core.logging`) |
| Rate limiting | Auth + webhook/tool paths when `SIGNALFLOW_RATE_LIMIT_ENABLED=true` |
| Security headers | nosniff, frame deny, referrer-policy, permissions-policy, baseline CSP |
| Cookies | HttpOnly session cookies; production requires `AUTH_COOKIE_SECURE=true` |
| CORS | Single configured `SIGNALFLOW_FRONTEND_ORIGIN` with credentials |

## Threats acknowledged

1. **Client-supplied `business_id` on open routes** — Retell tool endpoints ignore caller-supplied business IDs.
2. **Unsigned webhooks in mock mode** — acceptable only with `INTEGRATION_MODE=mock` and empty secrets.
3. **Legacy owner token** — `OWNER_API_TOKEN` / headers remain for CLI/bootstrap only; dashboard uses cookies.

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

## CORS audit

- Allowlist is a single origin (`SIGNALFLOW_FRONTEND_ORIGIN`), not `*`.
- `allow_credentials=True` requires exact origin match for cookie sessions.
- Production startup rejects localhost origins.

## Cookie configuration

| Cookie | HttpOnly | Secure (prod) | SameSite |
|--------|----------|---------------|----------|
| `sf_access` | yes | required | lax (see `app.core.cookies`) |
| `sf_refresh` | yes | required | lax |

Never store JWTs in `localStorage`.

## CSP recommendations

Frontend nginx (`frontend/nginx.conf`) ships a baseline CSP. Tighten further per deploy:

- `default-src 'self'`
- `connect-src 'self' https://api.yourdomain.com`
- `img-src 'self' data:`
- Avoid `unsafe-inline` scripts once nonces are practical

API responses also set a conservative CSP via `SecurityHeadersMiddleware`.

## Dependency audit

```bash
cd backend && pip install -e ".[dev]" && pip-audit || true
cd frontend && npm audit --omit=dev
```

Run in CI periodically; fix high/critical before go-live.

## Secrets audit

- `.env` gitignored; never commit provider keys
- Encrypted integration credentials at rest
- Production fail-fast on missing `JWT_SECRET` / encryption key
- Demo passwords only in [demo-data.md](demo-data.md) for non-prod

## Recommended next controls

- Multi-business memberships beyond single `users.business_id`
- Redis-backed rate limits for multi-instance
- Mandatory webhook signatures in all non-dev environments
- External WAF in front of auth/webhooks (AWS/Cloudflare)
