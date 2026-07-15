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
        return {"Authorization": f"Bearer {self.api_key}"}

    def list_agents(self) -> list[dict[str, Any]]:
        payload = request_json(
            self.settings,
            method="GET",
            url=f"{self.base_url}/list-agents",
            headers=self._headers(),
            params={"limit": 1000, "is_latest": "true"},
            retryable=True,
        )
        if isinstance(payload, list):
            return payload
        return payload.get("agents") or payload.get("items") or []

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
