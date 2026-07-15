# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `0.x` (main) | Active development — report issues against `main` |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive reports.

1. Email or privately contact the repository owner for [GoGitJC](https://github.com/GoGitJC) via GitHub Security Advisories on this repository (preferred when enabled).
2. Include: affected component, reproduction steps, impact, and any suggested fix.
3. Allow reasonable time for a patch before public disclosure.

## Secrets and credentials

If you accidentally commit secrets:

1. Rotate the credential immediately with the provider.
2. Contact maintainers to purge the secret from git history if it was pushed.
3. Never re-commit the same secret.

## Scope

In scope: authentication design (once shipped), webhook signature handling, tenancy isolation bugs, secret leakage, dependency CVEs in first-party configs.

Out of scope for this MVP phase: expecting production-grade auth on the current client-supplied `business_id` trust model — treat that as a known limitation, not a silent bug.
