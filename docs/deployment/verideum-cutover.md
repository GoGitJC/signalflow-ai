# Verideum temporary deployment & DNS cutover notes

## Manual deploy (CLIs not authenticated in this environment)

### Vercel frontend

1. Install/login: `npm i -g vercel && vercel login`
2. From `frontend/`: `vercel` (link project), then `vercel --prod`
3. Set Production env: `VITE_API_URL=https://api.verideum.com` (or temporary Render URL first)
4. Root directory: `frontend`
5. Build: `npm run build` · Output: `dist` · SPA rewrites already in `vercel.json`

### Render backend + Postgres

1. Open https://dashboard.render.com → New → Blueprint → connect `GoGitJC/signalflow-ai`
2. Apply `render.yaml` (creates `verideum-api` + `verideum-db`)
3. Set secrets in dashboard (never commit):
   - `SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY`
   - `OWNER_API_TOKEN`
   - `RETELL_*` / `CALCOM_*` as needed
4. Confirm `ALLOW_LIVE_BOOKING=false`
5. After first deploy, note temporary URL: `https://verideum-api.onrender.com`
6. Add custom domain `api.verideum.com` only after health checks pass

## Namecheap DNS (do not apply until temporary deploys are healthy)

| Type | Host | Value | TTL | Notes |
|------|------|-------|-----|-------|
| CNAME | `app` | Vercel DNS target from Vercel Domains UI | Automatic / 300 | Remove any parking CNAME for `app` |
| CNAME | `www` | Same Vercel target **or** redirect to apex | 300 | Remove parking/www conflicts |
| URL Redirect | `@` | `https://app.verideum.com` (temporary) or marketing later | — | Apex often uses redirect at Namecheap |
| CNAME | `api` | `verideum-api.onrender.com` (exact host from Render) | 300 | Remove conflicting `api` records |

Cloudflare: use only if already on the domain; otherwise stay on Namecheap DNS for this cutover.

## Retell cutover (after api.verideum.com is live)

Keep current tunnel URLs until production `/health` and `/ready` pass.

Production targets:

- Webhook: `https://api.verideum.com/api/webhooks/retell`
- `check_availability`: `https://api.verideum.com/api/retell/tools/check_availability`
- `book_appointment`: `https://api.verideum.com/api/retell/tools/book_appointment`

Sequence:

1. Verify production backend health + CORS from `app.verideum.com`
2. Update Retell agent webhook + LLM tool URLs
3. One non-booking call
4. Confirm call in production dashboard
5. Controlled live book only with explicit approval
6. Restore `ALLOW_LIVE_BOOKING=false`
