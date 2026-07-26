# Verideum — Launch Checklist

Public production launch gate. Complete every item (or explicitly waive with owner sign-off).

**Domain placeholder:** `<DOMAIN>`  
**Do not deploy until human approval.**

---

## Infrastructure

- [ ] Domain purchased
- [ ] DNS configured (Cloudflare `www`, `api`, optional `app` / `docs`)
- [ ] Backend deployed (Render)
- [ ] Frontend deployed (Vercel)
- [ ] Database deployed (Render PostgreSQL)
- [ ] HTTPS enabled (Full strict + Always HTTPS)
- [ ] Cookies secure (`AUTH_COOKIE_SECURE=true`, HttpOnly)
- [ ] CORS origins set to production dashboard URLs
- [ ] Trusted hosts configured for API

## Integrations

- [ ] Retell connected
- [ ] Cal.com connected
- [ ] Twilio connected (or explicitly deferred with owner waiver)
- [ ] Webhook URLs point at `https://api.<DOMAIN>/…`
- [ ] Webhook signatures verified in live mode

## Observability & data

- [ ] Health endpoints passing (`/health`, `/live`, `/ready`)
- [ ] Metrics enabled (`/metrics` scraped or reviewed)
- [ ] Backup configured
- [ ] Restore tested
- [ ] Demo tenant available (non-production / sales env)
- [ ] Final Production Acceptance complete (`ALLOW_LIVE_BOOKING` policy decided)

## Go / No-Go

| Sign-off | Name | Date |
|----------|------|------|
| Engineering | | |
| Product / founder | | |
| Deploy approver | | |

**Decision:** ☐ GO  ☐ NO-GO

---

Detailed runbooks: [docs/deployment/checklist.md](docs/deployment/checklist.md)
