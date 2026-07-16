# Demo data

Realistic demo tenant for sales and training.

## Seed command

```bash
# Compose
docker compose run --rm backend python -m app.cli.seed_demo

# Reset and re-seed
docker compose run --rm backend python -m app.cli.seed_demo --reset
```

## Login

| Field | Value |
|-------|-------|
| Email | `owner@alamodental-demo.example` |
| Password | `DemoPass123!` |
| Business | Alamo Dental Demo |

Use only in non-production environments.

## What is populated

- Dental business profile (hours, metro service area, phones)
- Owner user (verified email)
- Voice agent config (greeting + prompt)
- Callers (realistic names/phones)
- Calls with transcripts, AI summaries, outcomes
- Appointments across upcoming/past windows
- Knowledge-base FAQ entries

Enough volume for Overview, Calls, Appointments, Customers, and Analytics to look “live.”

## Notes

- Does not enable live Retell/Cal.com bookings.
- Safe to re-run; use `--reset` to wipe the demo business and recreate.
- Do not seed production customer databases with this CLI.
