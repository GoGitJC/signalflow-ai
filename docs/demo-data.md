# Demo data

Realistic HVAC demo tenant for closed-beta sales and training.

## Seed command

```bash
docker compose run --rm backend python -m app.cli.seed_demo
# wipe and recreate
docker compose run --rm backend python -m app.cli.seed_demo --reset
```

## Login

| Field | Value |
|-------|-------|
| Email | `owner@summithvac-demo.example` |
| Password | `DemoPass123!` |
| Business | Summit HVAC Pros |

Use only in non-production environments.

## What is populated

- HVAC business profile (Austin metro, hours, emergency forwarding)
- Owner user (verified email)
- Voice agent greeting + HVAC prompt
- Five callers with tags/notes
- Five calls with transcripts, AI summaries, intents, sentiment
- Appointments (diagnostic, tune-up, heat-pump estimate)
- Knowledge-base FAQs (hours, service area, pricing, brands, maintenance)

Enough volume for Overview, Calls, Appointments, Customers, and Analytics.

## Notes

- Does not enable live Retell/Cal.com bookings.
- Safe to re-run; use `--reset` to wipe the demo business and recreate.
- Do not seed production customer databases with this CLI.
