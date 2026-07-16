# Onboarding

First-run path for a new SignalFlow AI customer (operator).

## In-app wizard

After register, the dashboard routes to `/onboarding`:

1. **Connect Retell** — save API key, run connection test  
2. **Connect Cal.com** — save API key, run connection test  
3. **Connect Twilio** — record Account SID / token for later live SMS (gated until production acceptance)  
4. **Add knowledge** — create the first FAQ entry  
5. **Test voice agent** — open Voice Agent settings; place a no-booking test call with `ALLOW_LIVE_BOOKING=false`

Skip any step and finish later under **Settings**.

## Operator checklist

- [ ] Create owner account (register) or use demo seed login  
- [ ] Confirm cookie session works (`/api/auth/me`)  
- [ ] Set business profile (hours, phone, forwarding)  
- [ ] Connect Retell + map agent ID  
- [ ] Register public webhook URL with Retell (`APP_PUBLIC_API_URL`)  
- [ ] Connect Cal.com event type (keep live booking off until acceptance)  
- [ ] Add ≥3 knowledge-base entries  
- [ ] Simulate or place a test call; confirm call appears on dashboard  
- [ ] Invite a staff user if needed  
- [ ] Review Help page for mock webhook simulation in local/mock mode  

## Engineering setup (before customer day)

See [deployment.md](deployment.md) and [environment-variables.md](environment-variables.md). Production must pass startup validation (`JWT_SECRET`, encryption key, non-localhost CORS origin, secure cookies).

## Demo tenant

For sales demos without live providers: [demo-data.md](demo-data.md).
