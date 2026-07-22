# Deep rename plan (Verideum) — NOT EXECUTED

User-facing branding is **Verideum**. Technical identifiers still use historical `signalflow` / `SIGNALFLOW_` names. Defer deep rename until after domain cutover is stable.

| Area | Current | Future candidate | Risk |
|------|---------|------------------|------|
| GitHub repo | `signalflow-ai` | `verideum` | High (links, CI) |
| Python package name | `signalflow-backend` | `verideum-backend` | High |
| Frontend package name | `signalflow-dashboard` | `verideum-dashboard` | Medium |
| Env prefix | `SIGNALFLOW_` | `VERIDEUM_` | High (all deploys) |
| DB / Docker names | `signalflow` | `verideum` | High |
| Cookie names | `sf_access` / `sf_refresh` | `vd_*` | Medium (session reset) |
| Loggers | `signalflow.*` | `verideum.*` | Low |
| Domains | tunnels / localhost | `verideum.com` / `app` / `api` | See deployment checklist |

Do not execute this plan during branding-only or live-demo sprints.
