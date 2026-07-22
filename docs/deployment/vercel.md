# Vercel frontend deployment

Production dashboard for Verideum runs on **Vercel** as a Vite SPA.

> **Do not deploy until a human approves.** This document is configuration-only.

## Architecture role

```text
www.<DOMAIN> / app.<DOMAIN>  →  Cloudflare  →  Vercel (static React)
         │
         └── HTTPS fetch → https://api.<DOMAIN>  (credentials: include)
```

## Prerequisites

- Vercel account linked to GitHub
- Production API URL known (`https://api.<DOMAIN>`)
- Cloudflare DNS ready ([cloudflare.md](cloudflare.md))

## Project settings

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Framework | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm ci` |
| Node | 20.x |

Config file: [`frontend/vercel.json`](../../frontend/vercel.json)

## Environment variables

Set under **Project → Settings → Environment Variables** for **Production**:

| Variable | Example |
|----------|---------|
| `VITE_API_URL` | `https://api.<DOMAIN>` |

Optional: `VITE_BUSINESS_ID` only for single-tenant demos (prefer cookie session + server membership).

Template: [`frontend/.env.production.example`](../../frontend/.env.production.example)

`VITE_*` values are **baked in at build time**. Redeploy after changing them.

## SPA routing

`vercel.json` rewrites all paths to `/index.html` so React Router deep links work (`/calls/:id`, `/settings`, `/readiness`, etc.).

## Compression & caching

- Vercel enables gzip/brotli by default.
- `/assets/*` hashed bundles: `Cache-Control: public, max-age=31536000, immutable`
- `index.html`: `must-revalidate` so clients pick up new asset hashes quickly

## Security headers

Configured in `vercel.json`:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Content-Security-Policy` — **replace `api.YOUR_DOMAIN` with `api.<DOMAIN>` before go-live**
- `Strict-Transport-Security`

## Domains

1. Add `www.<DOMAIN>` (and optionally `app.<DOMAIN>`) in Vercel
2. Point Cloudflare CNAME to Vercel (see [cloudflare.md](cloudflare.md))
3. Enable HTTPS (Vercel + Cloudflare Always HTTPS)

## Cookie / CORS notes

- Dashboard origin must appear in backend `CORS_ORIGINS`
- Sessions use HttpOnly cookies on the **API host** (`api.<DOMAIN>`) with `credentials: "include"`
- `www` and `api` on the same eTLD+1 are same-site → `AUTH_COOKIE_SAMESITE=lax` is correct

## Deploy

1. Import GitHub repo in Vercel
2. Set root `frontend` + `VITE_API_URL`
3. Update CSP host in `vercel.json`
4. Deploy Production
5. Attach custom domains
6. Smoke: open `https://www.<DOMAIN>/login`, sign in, confirm network calls go to `https://api.<DOMAIN>`

## Preview deployments

Vercel Preview URLs need temporary CORS allowlisting if you test previews against production API — prefer a staging API instead.
