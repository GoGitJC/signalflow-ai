# Dashboard product guide

Verideum’s dashboard is the daily operating surface for owners and staff: CRM, call intelligence, appointments, analytics, voice configuration, knowledge, and settings.

## Navigation

| Page | Purpose |
|------|---------|
| Overview | At-a-glance metrics, recent calls, upcoming appointments |
| Customers | CRM directory with notes, tags, status, and history |
| Calls | Gong-style call list + expandable transcript detail |
| Appointments | Filterable booking list (upcoming / past / status) |
| Analytics | Executive metrics, funnel, lead sources, date ranges |
| Voice Agent | Greeting, prompt, voice, temperature, transfer rules |
| Knowledge | Searchable FAQ editor with bulk import and versions |
| Settings | Business profile, integrations, security, audit log |
| Help | Local setup shortcuts |

## Data loading

- TanStack Query caches tenant reads (`calls`, `appointments`, `knowledge`, `callers`, `analytics`, `voiceAgents`).
- Auth: Bearer JWT (preferred) or legacy `X-Owner-Token` + `X-Business-Id`.
- Set `VITE_BUSINESS_ID` and either JWT in localStorage or `VITE_OWNER_API_TOKEN`.

## Customer CRM

Each caller record supports:

- Search and status filters (`lead`, `customer`, `closed`)
- Lifetime call / appointment counts
- Last interaction timestamp
- Notes and tags (PATCH `/api/callers/{id}`)
- Linked recent calls and appointments

## Call intelligence

Detail view includes summary, expandable transcript, AI actions (intent / urgency / sentiment / outcome), timeline, appointment badge, and recording player when `recording_url` is present.

## Analytics ranges

`GET /api/businesses/{id}/analytics/summary?range=7d|30d|month`

Returns calls today, bookings, conversion, average duration, missed calls, transfers, AI resolution rate, booking funnel, lead sources, and time series.

## Voice agent

Configuration is persisted via `PATCH /api/voice-agents/{id}` (greeting, system prompt, voice, temperature, transfer number/rules, active). Syncing edits live to Retell remains a follow-up.

## Knowledge base

- Categories + search
- Markdown-friendly answers with preview
- Bulk import (`POST .../knowledge-base/bulk`)
- Version history (`GET /api/knowledge-base/{id}/versions`)

## UX system

Toasts, skeletons, empty states, and error retry are shared across pages. See [ui.md](ui.md).
