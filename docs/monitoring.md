# Monitoring

Production monitoring preparation for SignalFlow AI.

## Built-in metrics (`GET /metrics`)

Prometheus-compatible text exposition (in-process counters/histograms):

| Metric | Meaning |
|--------|---------|
| `signalflow_http_requests_total` | Requests by method, family (`auth`/`webhook`/`booking`/`other`), status |
| `signalflow_http_request_duration_ms` | Latency histogram by family |
| `signalflow_http_errors_total` | 5xx count by family |
| `signalflow_webhook_requests_total` | Webhook traffic |
| `signalflow_booking_requests_total` | Booking-related path hits |

Scrape `/metrics` from Prometheus, Grafana Agent, Datadog, or similar. Protect the endpoint at the edge if the API is public (IP allowlist or auth proxy).

## Suggested alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| API down | `/live` fails 2m | Page on-call; check deploy/crash loops |
| Not ready | `/ready` fails 2m | Check Postgres connectivity/credentials |
| Error rate | `5xx` > 2% for 5m | Inspect logs by `request_id`; check providers |
| Webhook spike / drop | webhook RPS anomaly | Verify Retell/Cal.com status + signatures |
| Auth pressure | auth 429 surge | Possible credential stuffing — confirm rate limits |
| Latency | p95 duration > 2s | DB load, external API latency |

## Logs

- JSON logs with `request_id`, method, path, status, duration.
- Correlate dashboard errors (`error.request_id`) with API logs.
- Never ship secrets into log aggregators; redact PII.

## Dashboards (first customer)

Minimum panels:

1. Request rate + error rate
2. p50/p95 latency
3. Webhook success vs 4xx/5xx
4. Booking path volume (even when `ALLOW_LIVE_BOOKING=false`)
5. Auth login failures (from status codes / audit table)

## External uptime

Point a synthetic check at `/health` every 60s from outside the VPC. Use `/ready` for deploy gates, not for public uptime (DB blips should not always page as “site down”).
