# Retell AI integration

## Role

Retell provides the voice agent. SignalFlow maps each Retell agent to one business, ingests webhooks, and exposes tool endpoints for availability and booking.

## Credentials

| Variable | Purpose |
|----------|---------|
| `RETELL_API_KEY` | Retell REST API (use the key with the webhook badge for signature verification) |
| `RETELL_AGENT_ID` | Optional — verify a specific agent |
| `RETELL_AGENT_NAME` | Exact display name match (default `Universal_Demo`) |
| `RETELL_WEBHOOK_BASE_URL` | Public base URL for proposed webhook (falls back to `APP_PUBLIC_API_URL`) |
| `RETELL_WEBHOOK_SECRET` | Legacy HMAC bypass for mock mode only |
| `INTEGRATION_MODE` | `mock` (default) or `live` |

Per-business credentials are stored encrypted in `integrations` (provider `retell`). Environment variables bootstrap the owner workspace locally.

## Resolve agent ID

```bash
INTEGRATION_MODE=live RETELL_API_KEY=... RETELL_AGENT_NAME=Universal_Demo \
  python -m app.cli.resolve_retell_agent
```

Optional verification:

```bash
python -m app.cli.resolve_retell_agent --agent-id <id> --agent-name Universal_Demo
```

## Webhook URLs

| Level | URL |
|-------|-----|
| Unified (recommended) | `{APP_PUBLIC_API_URL}/api/webhooks/retell` |
| Legacy call-started | `{APP_PUBLIC_API_URL}/api/webhooks/retell/call-started` |
| Legacy call-ended | `{APP_PUBLIC_API_URL}/api/webhooks/retell/call-ended` |

Agent-level webhooks override account-level webhooks for that agent ([Retell docs](https://docs.retellai.com/features/webhook-overview)).

**Do not change live Retell webhook settings until you review the proposed URL.**

## Signature verification

Header: `X-Retell-Signature` format `v={timestamp_ms},d={hex_digest}`

Live mode (`INTEGRATION_MODE=live`):

1. Parse timestamp and digest from the header
2. Reject if timestamp is older than 5 minutes
3. Compute `HMAC-SHA256(raw_body + timestamp, RETELL_API_KEY)`
4. Compare digest to `d`

Mock mode:

- Skips verification when `RETELL_WEBHOOK_SECRET` is empty
- Supports legacy `sha256=` HMAC with `RETELL_WEBHOOK_SECRET` for local fixtures

Use the **raw request body** — re-serialized JSON will fail verification.

## Management API (owner/admin)

Headers: `X-Owner-Token`, `X-Business-Id`

| Method | Path |
|--------|------|
| `GET` | `/api/integrations/retell/status` |
| `PUT` | `/api/integrations/retell` |
| `POST` | `/api/integrations/retell/test` |

API keys are never returned after save. Responses include masked agent IDs only.

## Retell tool endpoints

Business is resolved from `retell_agent_id` via `voice_agents` — never trust arbitrary `business_id` from the agent payload.

| Method | Path |
|--------|------|
| `POST` | `/api/retell/tools/check_availability` |
| `POST` | `/api/retell/tools/book_appointment` |

## Events handled

| Event | Behavior |
|-------|----------|
| `call_started` | Create call row |
| `call_ended` | Upsert caller, call, optional appointment |
| `call_analyzed` | Same as call-ended with analysis fields when present |

Idempotency uses `webhook_events` keyed by `call_id` + event.

## Local tunnel

Expose webhooks with ngrok, Cloudflare Tunnel, or similar:

```bash
ngrok http 8000
# Set APP_PUBLIC_API_URL=https://<subdomain>.ngrok-free.app
```

## Create a Retell API key

1. Open [Retell dashboard](https://dashboard.retellai.com/)
2. Settings → API Keys
3. Create a key with the **webhook** badge for signature verification
4. Store in `.env` as `RETELL_API_KEY` (never commit)

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `Invalid webhook signature` | Raw body, correct API key, clock skew < 5 min |
| `No business mapped to Retell agent` | Run connection test or insert `voice_agents` row |
| Multiple agents named `Universal_Demo` | Set `RETELL_AGENT_ID` explicitly |

## Local simulation

```bash
BUSINESS_ID=<uuid> ./scripts/simulate_call.sh
```

## Live-ready tool endpoints

| Method | Path |
|--------|------|
| `POST` | `/api/retell/tools/check_availability` |
| `POST` | `/api/retell/tools/book_appointment` |

`check_availability` returns voice-friendly `options` with `option_id` + `spoken_summary`.
`book_appointment` requires `caller_confirmed=true` and resolves business from `retell_agent_id` only.

Retell custom functions POST an envelope `{ "call": {...}, "name": "...", "args": {...} }`.
These endpoints unwrap `args` (and fall back to `call.agent_id` / `call.call_id` when needed).
Flat JSON bodies are still accepted for local tests and scripts.

Acceptance notes (no-booking gate verified live; Phase C email-input issue documented): [live-acceptance-2026-07-16.md](./live-acceptance-2026-07-16.md).

Do not configure these as live Retell custom functions until the public webhook/tool base URL is approved.

## Persist mapping

```bash
python scripts/prepare_integration_keys.py   # local .env only
docker compose up -d --force-recreate backend
docker compose exec backend python -m app.cli.sync_live_integrations --business-id "$VITE_BUSINESS_ID"
```

## Manual verification (no real booking)

```bash
./scripts/verify_integrations.sh
```
