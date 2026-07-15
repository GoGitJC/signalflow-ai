"""Resolve Retell agent ID by display name without exposing secrets."""

from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings
from app.integrations.errors import ProviderError
from app.integrations.factory import get_retell_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a Retell agent by display name")
    parser.add_argument("--agent-name", default=None, help="Exact case-sensitive display name")
    parser.add_argument("--agent-id", default=None, help="Optional agent ID to verify")
    args = parser.parse_args()

    settings = get_settings()
    settings.require_live_retell_config()
    agent_name = args.agent_name or settings.retell_agent_name
    client = get_retell_client(settings=settings)
    try:
        resolved = client.resolve_agent(agent_id=args.agent_id or settings.retell_agent_id or None, agent_name=agent_name)
    except ProviderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"agent_id={resolved['agent_id']}")
    print(f"agent_name={resolved['agent_name']}")
    if resolved.get("webhook_url"):
        print(f"current_webhook_url={resolved['webhook_url']}")
    print(f"proposed_webhook_url={settings.retell_webhook_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
