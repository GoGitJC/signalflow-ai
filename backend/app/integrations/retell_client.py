from typing import Any, cast

from app.core.config import Settings, get_settings
from app.integrations.errors import (
    ProviderConflictError,
    ProviderNotFoundError,
    ProviderValidationError,
)
from app.integrations.http_utils import request_json


class RetellClient:
    base_url = "https://api.retellai.com"

    def __init__(self, api_key: str, settings: Settings | None = None):
        self.api_key = api_key
        self.settings = settings or get_settings()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_agents(self, *, channel: str = "voice", limit: int = 100) -> list[dict[str, Any]]:
        """List agents via POST /v2/list-agents (GET /list-agents is deprecated)."""
        agents: list[dict[str, Any]] = []
        pagination_key: str | None = None
        # Cap pages to avoid runaway loops on malformed has_more.
        for _ in range(50):
            body: dict[str, Any] = {
                "filter_criteria": {
                    "channel": {
                        "op": "eq",
                        "value": channel,
                    }
                },
                "limit": limit,
            }
            if pagination_key:
                body["pagination_key"] = pagination_key

            payload = request_json(
                self.settings,
                method="POST",
                url=f"{self.base_url}/v2/list-agents",
                headers=self._headers(),
                json_body=body,
                retryable=True,
            )
            if not isinstance(payload, dict):
                raise ProviderValidationError("Malformed Retell list-agents response")

            items = payload.get("items")
            if items is None:
                # Defensive: older shapes should not be treated as success for v2.
                raise ProviderValidationError("Retell list-agents response missing items")
            if not isinstance(items, list):
                raise ProviderValidationError("Retell list-agents items must be a list")

            agents.extend(cast(list[dict[str, Any]], items))

            if not payload.get("has_more"):
                break
            next_key = payload.get("pagination_key")
            if not isinstance(next_key, str) or not next_key:
                break
            pagination_key = next_key

        return agents

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        payload = request_json(
            self.settings,
            method="GET",
            url=f"{self.base_url}/get-agent/{agent_id}",
            headers=self._headers(),
            retryable=True,
        )
        return cast(dict[str, Any], payload)

    def resolve_agent(self, *, agent_id: str | None, agent_name: str) -> dict[str, Any]:
        if agent_id:
            agent = self.get_agent(agent_id)
            display = agent.get("agent_name") or agent.get("name")
            if display != agent_name:
                raise ProviderValidationError(
                    f"Retell agent {agent_id} display name '{display}' does not match '{agent_name}'"
                )
            return {
                "agent_id": agent.get("agent_id") or agent_id,
                "agent_name": display,
                "webhook_url": agent.get("webhook_url"),
            }

        matches = [
            agent
            for agent in self.list_agents()
            if (agent.get("agent_name") or agent.get("name")) == agent_name
        ]
        if not matches:
            raise ProviderNotFoundError(f"No Retell agent found with display name '{agent_name}'")
        if len(matches) > 1:
            ids = [m.get("agent_id") or m.get("id") for m in matches]
            raise ProviderConflictError(
                f"Multiple Retell agents named '{agent_name}': {', '.join(str(i) for i in ids)}"
            )
        agent = matches[0]
        return {
            "agent_id": agent.get("agent_id") or agent.get("id"),
            "agent_name": agent.get("agent_name") or agent.get("name"),
            "webhook_url": agent.get("webhook_url"),
        }

    def test_connection(self, *, agent_id: str | None, agent_name: str) -> dict[str, Any]:
        resolved = self.resolve_agent(agent_id=agent_id, agent_name=agent_name)
        return {
            "ok": True,
            "agent_id": resolved["agent_id"],
            "agent_name": resolved["agent_name"],
            "webhook_url": resolved.get("webhook_url"),
        }
