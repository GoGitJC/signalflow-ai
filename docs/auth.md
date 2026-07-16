# Authentication

SignalFlow uses **HttpOnly cookie sessions** for the dashboard. JWTs are never stored in `localStorage`.

## Session cookies

| Cookie | Purpose | Lifetime |
|--------|---------|----------|
| `sf_access` | Short-lived access JWT | `JWT_ACCESS_TTL_MINUTES` (default 30) |
| `sf_refresh` | Rotating refresh token | `JWT_REFRESH_TTL_DAYS` / remember-me days |

Flags: `HttpOnly`, `SameSite` (`AUTH_COOKIE_SAMESITE`, default `lax`), `Secure` when `AUTH_COOKIE_SECURE=true`.

CORS allows credentials from `SIGNALFLOW_FRONTEND_ORIGIN`.

## Routes

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/auth/register` | Creates business + owner; sets cookies |
| `POST` | `/api/auth/login` | Email/password; optional `remember_me` |
| `POST` | `/api/auth/refresh` | Cookie refresh rotation |
| `POST` | `/api/auth/logout` | Revokes refresh + clears cookies |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/auth/forgot-password` | Issues reset token (returned in dev) |
| `POST` | `/api/auth/reset-password` | Sets new password; revokes sessions |
| `POST` | `/api/auth/verify-email` | Placeholder verification |
| `GET/POST` | `/api/auth/users`, `/invitations` | Admin user directory + invites |
| `POST` | `/api/auth/invitations/accept` | Accept invite → session cookies |

## Frontend

- `AuthProvider` / `useAuth()`
- `ProtectedRoute`, `GuestRoute`, `RoleGuard`, `PermissionGuard`
- Automatic refresh interceptor on `401`
- Periodic background refresh
- Pages: login, register, forgot/reset password, verify email, session expired, unauthorized, accept invite

Legacy `X-Owner-Token` remains for bootstrap/CLI/tests only — the dashboard no longer uses it.
