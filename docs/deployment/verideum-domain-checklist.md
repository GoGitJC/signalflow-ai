# Verideum domain & deployment checklist

Owned domain: **verideum.com**

Target hostnames:

| Host | Role |
|------|------|
| `https://verideum.com` | Marketing / landing (optional) |
| `https://www.verideum.com` | Marketing alias |
| `https://app.verideum.com` | React dashboard (Vercel) |
| `https://api.verideum.com` | FastAPI backend (Render) |

Do **not** change DNS until branding is merged and you explicitly approve cutover.

---

## 1. Namecheap DNS

In Namecheap → Domain List → **verideum.com** → Advanced DNS:

1. Prefer pointing nameservers to **Cloudflare** (recommended) *or* keep Namecheap DNS and create records below.
2. If staying on Namecheap DNS (no Cloudflare proxy):
   - `CNAME` `www` → Vercel project domain (from Vercel UI)
   - `CNAME` `app` → Vercel project domain
   - `CNAME` `api` → Render service hostname (e.g. `verideum-api.onrender.com`)
   - `@` (Apex): use Namecheap URL redirect to `https://www.verideum.com` **or** Vercel/Cloudflare apex instructions
3. Remove conflicting parking / placeholder records before go-live.
4. TTL: 300s during cutover, raise later.

---

## 2. Cloudflare (recommended)

1. Add site **verideum.com** to Cloudflare.
2. Update Namecheap nameservers to the Cloudflare pair Cloudflare provides.
3. SSL/TLS mode: **Full (strict)** once Render/Vercel certs are active.
4. DNS records (proxied orange-cloud for web; follow Render docs if API needs grey-cloud):

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | `app` | Vercel DNS target | Proxied |
| CNAME | `www` | Vercel DNS target | Proxied |
| CNAME | `api` | `*.onrender.com` service host | Per Render guidance |
| Apex | `@` | Vercel/Cloudflare apex setup | Proxied |

5. Enable **Always Use HTTPS**.
6. Optional: HSTS only after HTTPS is verified on all hosts.

---

## 3. Vercel frontend

1. Import GitHub repo; Root Directory = `frontend`.
2. Framework: Vite. Build: `npm run build`. Output: `dist`.
3. Domains: add `app.verideum.com` (and optionally `verideum.com` / `www`).
4. Environment (Production):
   - `VITE_API_URL=https://api.verideum.com`
5. Confirm preview deployments still work on `*.vercel.app`.
6. After DNS: Vercel → Domains → verify SSL issued.

---

## 4. Render backend

1. Blueprint or Web Service from repo; Root = `backend` (or use `render.yaml`).
2. Runtime: Docker or native Python 3.12.
3. Attach **Render PostgreSQL**.
4. Set env from [`.env.production.example`](../../.env.production.example), especially:
   - `SIGNALFLOW_ENVIRONMENT=production`
   - `APP_PUBLIC_API_URL=https://api.verideum.com`
   - `CORS_ORIGINS=https://verideum.com,https://www.verideum.com,https://app.verideum.com`
   - `SIGNALFLOW_FRONTEND_ORIGIN=https://app.verideum.com`
   - `TRUSTED_HOSTS=api.verideum.com,...`
   - `AUTH_COOKIE_SECURE=true`
   - `ALLOW_LIVE_BOOKING=false`
   - secrets: `JWT_SECRET`, encryption key, Retell/Cal.com keys
5. Custom domain: `api.verideum.com` → verify DNS → wait for cert.
6. Health check path: `/health` (or `/ready`).
7. Run Alembic migrations on deploy.

---

## 5. PostgreSQL

1. Provision Render Postgres (or external).
2. Ensure `SIGNALFLOW_DATABASE_URL` uses `postgresql+psycopg://…`.
3. Backup before first production migrate.
4. Do **not** seed demo passwords into production customer DB without approval.
5. Confirm one Alembic head after migrate.

---

## 6. SSL

| Host | Issuer | Check |
|------|--------|-------|
| `app.verideum.com` | Vercel | `https://app.verideum.com` loads dashboard |
| `api.verideum.com` | Render | `https://api.verideum.com/health` → 200 |
| `www` / apex | Vercel/Cloudflare | HTTPS redirect works |

Cloudflare SSL/TLS must be **Full (strict)** when origin certs exist.

---

## 7. Domain verification & cutover smoke test

- [ ] DNS propagated (`dig app.verideum.com`, `dig api.verideum.com`)
- [ ] Frontend login at `https://app.verideum.com`
- [ ] API CORS allows `app.verideum.com` (browser login works)
- [ ] Cookies set with `Secure` on HTTPS
- [ ] Retell webhook URL = `https://api.verideum.com/api/webhooks/retell`
- [ ] Retell tools:
  - `https://api.verideum.com/api/retell/tools/check_availability`
  - `https://api.verideum.com/api/retell/tools/book_appointment`
- [ ] Cal.com credentials still resolve
- [ ] `ALLOW_LIVE_BOOKING=false` unless an approved live test
- [ ] Localhost demo still works: `http://localhost:5173` + `http://localhost:8000`

---

## Explicit non-goals (this checklist)

- Do **not** auto-deploy from this document.
- Do **not** change Namecheap/Cloudflare DNS until approved.
- Do **not** rename GitHub repo / `SIGNALFLOW_*` env names / DB schemas in this pass.
