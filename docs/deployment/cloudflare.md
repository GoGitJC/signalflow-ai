# Cloudflare DNS & edge

Cloudflare sits in front of Vercel (dashboard) and Render (API).

> **Do not change live DNS until a human approves.**

## Target records

Replace `<DOMAIN>` and provider hostnames with your real values.

| Type | Name | Target | Proxy | Purpose |
|------|------|--------|-------|---------|
| CNAME | `www` | `cname.vercel-dns.com` (or Vercel-assigned) | Proxied (orange) | Dashboard |
| CNAME | `app` | same as `www` (optional alias) | Proxied | Alternate dashboard host |
| CNAME | `api` | `<service>.onrender.com` | Proxied or DNS-only* | FastAPI |
| CNAME | `docs` | optional static docs host | Proxied | Optional docs site |
| A/AAAA | `@` | Vercel A/AAAA or redirect to `www` | Proxied | Apex → www |

\*For Render custom domains, follow Render’s current guidance. If TLS issues appear with Cloudflare orange-cloud, temporarily set **DNS only** (grey cloud) until certificates stabilize, then re-enable proxy with **SSL/TLS Full (strict)**.

### A vs CNAME

- Use **CNAME** for `www`, `app`, `api`, `docs` when the target is a hostname (Vercel/Render).
- Use **A/AAAA** only when the provider gives static IPs (Vercel apex often uses A/AAAA + CNAME flattening via Cloudflare).

Cloudflare **CNAME flattening** lets you CNAME the apex (`@`) if desired.

## SSL/TLS

| Setting | Recommended value |
|---------|-------------------|
| SSL/TLS encryption mode | **Full (strict)** |
| Always Use HTTPS | **On** |
| Automatic HTTPS Rewrites | **On** |
| Minimum TLS Version | 1.2 |
| Opportunistic Encryption | On |
| TLS 1.3 | On |

Do **not** use Flexible SSL (browser→CF HTTPS, CF→origin HTTP) — breaks secure cookies and confuses origins.

## Caching

| Path | Recommendation |
|------|----------------|
| `www` / `app` static assets | Cache everything compatible with Vercel hashes; or bypass and let Vercel cache |
| `api.<DOMAIN>/*` | **Bypass cache** (API / cookies / webhooks) |
| `/api/webhooks/*` | Never cache; ensure Cloudflare does not challenge Retell/Cal.com POSTs |

Create a Cache Rule: hostname equals `api.<DOMAIN>` → Cache eligibility **Bypass**.

## Webhooks through Cloudflare

Retell and Cal.com POST to `https://api.<DOMAIN>/api/webhooks/...`.

- Disable Bot Fight Mode challenges on `/api/webhooks/*` if providers get 403
- Do not enable email obfuscation or Rocket Loader on API host
- Prefer WAF rate limits that allow provider IP ranges if available

## WAF / security (recommended)

- Rate limit `/api/auth/login` and `/api/auth/register`
- Rate limit `/api/webhooks/*` separately (higher, but capped)
- Block countries only if product requirements allow

## Verification

```bash
dig www.<DOMAIN> +short
dig api.<DOMAIN> +short
curl -I https://www.<DOMAIN>
curl -fsS https://api.<DOMAIN>/ready
```

Confirm certificate names match hosts and HSTS is present on both.
