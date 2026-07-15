# Contributing to SignalFlow AI

Thanks for contributing. GitHub is the authoritative project record for issues, pull requests, and releases.

## Development workflow

1. Fork or create a feature branch from `main`.
2. Use [conventional commits](https://www.conventionalcommits.org/) where practical (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`, `refactor:`).
3. Keep PRs focused; update docs and `CHANGELOG.md` for user-visible changes.
4. Ensure CI passes before requesting review.

## Local checks

```bash
# Backend
cd backend && pip install -e '.[dev]'
ruff check . && ruff format --check . && mypy && pytest

# Frontend
cd frontend && npm ci && npx tsc --noEmit && npm run build
```

## Pull requests

- Fill out the PR template.
- Link related issues.
- Do not include `.env`, credentials, dumps, `node_modules`, or virtualenvs.
- Screenshots for UI changes are appreciated (`docs/images/`).

## Branch protection (recommended for maintainers)

On `main`:

- Require a pull request
- Require these status checks:
  - **Backend quality**
  - **Frontend quality**
  - **Docker image builds**
- Require up-to-date branches before merge
- Disallow force push

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security issues

Do not open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the project [LICENSE](LICENSE).
