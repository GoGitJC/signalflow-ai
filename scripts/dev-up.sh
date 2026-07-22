#!/usr/bin/env bash
# Start the local Verideum stack from a clean slate (optional) or rebuild in place.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if [[ "${1:-}" == "--reset" ]]; then
  docker compose down -v
fi

docker compose up --build -d
echo "Waiting for backend health..."
for _ in $(seq 1 40); do
  if curl -sf http://localhost:8000/health >/dev/null; then
    echo "Backend healthy: http://localhost:8000/health"
    echo "Dashboard:       http://localhost:5173"
    echo "API docs:        http://localhost:8000/docs"
    exit 0
  fi
  sleep 2
done
echo "Backend did not become healthy in time; check: docker compose logs backend" >&2
exit 1
