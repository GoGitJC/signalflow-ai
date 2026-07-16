# Production deployment checklist

Use this runbook in order. **Do not deploy until human approval.**

## 0. Pre-flight (repo)

- [ ] CI green on target branch (`ruff`, `mypy`, `pytest`, frontend typecheck/build, Docker builds)
- [ ] `.env` / secrets **not** committed
- [ ] `ALLOW_LIVE_BOOKING=false` for first public cutover
- [ ] CSP host in `frontend/vercel.json` updated from `YOUR_DOMAIN`
- [ ] Domain purchased and Cloudflare zone active

## 1. Database (Render)

- [ ] Provision Render PostgreSQL 16
- [ ] Enable automated backups
- [ ] Note Internal Database URL
- [ ] Confirm URL normalization to `postgresql+psycopg://` (automatic in Settings)

## 2. Backend (Render)

- [ ] Create / apply Blueprint or Docker web service (`backend/`)
- [ ] Set all production env vars from [`.env.production.example`](../../.env.production.example)
- [ ] Health check = `/ready`
- [ ] Deploy succeeds; logs show migrations + startup
- [ ] `curl https://api.<DOMAIN>/live` → 200
- [ ] `curl https://api.<DOMAIN>/ready` → 200
- [ ] `curl https://api.<DOMAIN>/metrics` → text metrics

## 3. Frontend (Vercel)

- [ ] Project root `frontend`
- [ ] `VITE_API_URL=https://api.<DOMAIN>`
- [ ] Production build succeeds
- [ ] Custom domain `www.<DOMAIN>` (optional `app.<DOMAIN>`)
- [ ] SPA deep link works (refresh on `/settings`)

## 4. Cloudflare DNS / TLS

- [ ] `www` CNAME → Vercel
- [ ] `api` CNAME → Render
- [ ] SSL mode **Full (strict)**
- [ ] Always HTTPS + Automatic HTTPS Rewrites
- [ ] API cache **bypassed**
- [ ] Webhook paths not challenged by Bot Fight

## 5. Security

- [ ] `AUTH_COOKIE_SECURE=true`
- [ ] `AUTH_COOKIE_SAMESITE=lax`
- [ ] `CORS_ORIGINS` lists exact https dashboard origins
- [ ] `TRUSTED_HOSTS` set for API host
- [ ] Login sets HttpOnly cookies on `api.<DOMAIN>`
- [ ] Webhook signatures required in live mode
- [ ] No secrets in Git history for this release

## 6. Integrations

- [ ] Retell webhook URL = `https://api.<DOMAIN>/api/webhooks/retell`
- [ ] Cal.com webhook configured (if used)
- [ ] Twilio secrets present (SMS may still be gated)
- [ ] Connection tests OK from Settings
- [ ] Dashboard `/readiness` reviewed

## 7. Data / ops

- [ ] Backup schedule confirmed
- [ ] Restore drill documented / performed on staging
- [ ] Demo tenant seed available for sales (`python -m app.cli.seed_demo`) **non-prod only**
- [ ] On-call owner assigned
- [ ] Final Production Acceptance checklist tracked

## Related docs

- [render.md](render.md) · [vercel.md](vercel.md) · [cloudflare.md](cloudflare.md) · [disaster-recovery.md](disaster-recovery.md)
- [../LAUNCH_CHECKLIST.md](../../LAUNCH_CHECKLIST.md)
