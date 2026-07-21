from unittest.mock import patch

import httpx
import pytest

from app.integrations.errors import (
    ProviderAuthError,
    ProviderValidationError,
)
from app.integrations.retell_client import RetellClient


def test_list_agents_posts_v2_voice_filter():
    client = RetellClient("test-key")
    captured: dict = {}

    def fake_request_json(settings, **kwargs):
        captured.update(kwargs)
        return {"items": [{"agent_id": "a1", "agent_name": "Demo"}], "has_more": False}

    with patch("app.integrations.retell_client.request_json", side_effect=fake_request_json):
        agents = client.list_agents()

    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.retellai.com/v2/list-agents"
    assert captured["json_body"]["filter_criteria"]["channel"] == {
        "op": "eq",
        "value": "voice",
    }
    assert captured["json_body"]["limit"] == 100
    assert "pagination_key_version" not in captured["json_body"]
    assert agents[0]["agent_id"] == "a1"


def test_list_agents_parses_items_and_empty():
    client = RetellClient("test-key")
    with patch(
        "app.integrations.retell_client.request_json",
        return_value={"items": [], "has_more": False},
    ):
        assert client.list_agents() == []


def test_list_agents_pagination():
    client = RetellClient("test-key")
    calls: list[dict] = []

    def fake_request_json(settings, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {
                "items": [{"agent_id": "a1", "agent_name": "One"}],
                "has_more": True,
                "pagination_key": "page-2",
            }
        return {
            "items": [{"agent_id": "a2", "agent_name": "Two"}],
            "has_more": False,
            "pagination_key": "page-3",
        }

    with patch("app.integrations.retell_client.request_json", side_effect=fake_request_json):
        agents = client.list_agents()

    assert [a["agent_id"] for a in agents] == ["a1", "a2"]
    assert "pagination_key" not in calls[0]["json_body"]
    assert calls[1]["json_body"]["pagination_key"] == "page-2"
    assert "pagination_key_version" not in calls[1]["json_body"]


def test_list_agents_api_failure():
    client = RetellClient("bad-key")
    response = httpx.Response(401, json={"message": "Unauthorized"})
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = response
        with pytest.raises(ProviderAuthError):
            client.list_agents()


def test_list_agents_malformed_response():
    client = RetellClient("test-key")
    with patch("app.integrations.retell_client.request_json", return_value=["not", "a", "dict"]):
        with pytest.raises(ProviderValidationError):
            client.list_agents()

    with patch(
        "app.integrations.retell_client.request_json",
        return_value={"has_more": False},
    ):
        with pytest.raises(ProviderValidationError):
            client.list_agents()

    with patch(
        "app.integrations.retell_client.request_json",
        return_value={"items": "nope", "has_more": False},
    ):
        with pytest.raises(ProviderValidationError):
            client.list_agents()


def test_list_agents_never_uses_deprecated_get(monkeypatch):
    client = RetellClient("test-key")
    seen_urls: list[str] = []

    def fake_request_json(settings, **kwargs):
        seen_urls.append(f"{kwargs['method']} {kwargs['url']}")
        return {"items": [], "has_more": False}

    with patch("app.integrations.retell_client.request_json", side_effect=fake_request_json):
        client.list_agents()

    assert all("/list-agents" not in url or url.startswith("POST ") for url in seen_urls)
    assert any(url == "POST https://api.retellai.com/v2/list-agents" for url in seen_urls)
    assert not any(url.startswith("GET ") and "/list-agents" in url for url in seen_urls)
