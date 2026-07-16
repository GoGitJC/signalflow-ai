# Onboarding

First-run path for SignalFlow AI closed beta.

## In-app wizard (`/onboarding`)

1. **Welcome** — product overview and beta expectations  
2. **Connect Retell** — save API key, run connection test  
3. **Connect Cal.com** — save API key, run connection test  
4. **Connect Twilio** — placeholder notes (SMS gated until Final Acceptance)  
5. **Add knowledge** — create the first FAQ entry  
6. **Test call checklist** — verify greeting, webhook, no-booking test call, dashboard persistence  

Skip any step and finish later under **Settings**. Review **Acceptance** (`/readiness`) before go-live.

## Operator checklist

- [ ] Create owner account or use HVAC demo seed login  
- [ ] Confirm cookie session (`/api/auth/me`)  
- [ ] Complete onboarding wizard  
- [ ] Register public Retell webhook (`APP_PUBLIC_API_URL`)  
- [ ] Keep `ALLOW_LIVE_BOOKING=false` until Final Acceptance  
- [ ] Add ≥3 knowledge-base entries  
- [ ] Confirm a test call appears on the dashboard  
- [ ] Export CSV smoke test (Settings → Exports)  
- [ ] Invite a staff user if needed  

## Engineering setup

See [deployment.md](deployment.md) and [environment-variables.md](environment-variables.md). Production requires JWT secret, encryption key, non-localhost CORS, and secure cookies.

## Demo tenant

[demo-data.md](demo-data.md) — Summit HVAC Pros.
