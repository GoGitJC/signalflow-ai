# Deep rename plan (ForgeLinq) — NOT EXECUTED

Technical identifiers still use historical `signalflow` / `SIGNALFLOW_` names. Defer until after live booking acceptance.

| Area | Current | Future candidate | Risk |
|------|---------|------------------|------|
| GitHub repo | `signalflow-ai` | `forgelinq` | High (links, CI) |
| Python package / imports | `app` under signalflow repo | optional rename | High |
| Env prefix | `SIGNALFLOW_` | `FORGELINQ_` | High (all deploys) |
| DB / Docker names | `signalflow` | `forgelinq` | High |
| Cookie names | `sf_access` / `sf_refresh` | `fl_*` | Medium (session reset) |
| Loggers | `signalflow.*` | `forgelinq.*` | Low |

Do not execute this plan during the booking-repair sprint.
