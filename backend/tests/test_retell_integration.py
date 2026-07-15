from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException

from app.integrations.errors import (
    ProviderAuthError,
    ProviderConflictError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from app.integrations.retell_client import RetellClient
from app.integrations.retell_signature import verify_retell_signature
from tests.conftest import legacy_hmac_signature, retell_signature


def test_retell_resolve_agent_exact_match():
    client = RetellClient("test-key")
    agents = [
        {"agent_id": "a1", "agent_name": "Universal_Demo"},
        {"agent_id": "a2", "agent_name": "Other"},
    ]
    with patch("app.integrations.retell_client.request_json", return_value=agents):
        resolved = client.resolve_agent(agent_id=None, agent_name="Universal_Demo")
    assert resolved["agent_id"] == "a1"


def test_retell_resolve_agent_no_match():
    client = RetellClient("test-key")
    with patch("app.integrations.retell_client.request_json", return_value=[]):
        with pytest.raises(ProviderNotFoundError):
            client.resolve_agent(agent_id=None, agent_name="Universal_Demo")


def test_retell_resolve_agent_duplicate_match():
    client = RetellClient("test-key")
    agents = [
        {"agent_id": "a1", "agent_name": "Universal_Demo"},
        {"agent_id": "a2", "agent_name": "Universal_Demo"},
    ]
    with patch("app.integrations.retell_client.request_json", return_value=agents):
        with pytest.raises(ProviderConflictError):
            client.resolve_agent(agent_id=None, agent_name="Universal_Demo")


def test_retell_invalid_api_key_maps_to_auth_error():
    client = RetellClient("bad-key")
    response = httpx.Response(401, json={"message": "Unauthorized"})
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = response
        with pytest.raises(ProviderAuthError):
            client.list_agents()


def test_retell_timeout_maps_to_timeout_error():
    client = RetellClient("test-key")
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.side_effect = httpx.TimeoutException(
            "timeout"
        )
        with pytest.raises(ProviderTimeoutError):
            client.list_agents()


def test_retell_signature_success():
    body = '{"event":"call_ended"}'
    api_key = "retell-test-key"
    signature = retell_signature(body, api_key)
    verify_retell_signature(body, signature, api_key)


def test_retell_signature_invalid():
    body = '{"event":"call_ended"}'
    with pytest.raises(HTTPException):
        verify_retell_signature(body, "v=1,d=bad", "retell-test-key")


def test_retell_signature_missing():
    with pytest.raises(HTTPException):
        verify_retell_signature("{}", None, "retell-test-key")


def test_retell_webhook_duplicate_event(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    payload = {
        "event_id": "evt-call-ended-dup",
        "business_id": business["id"],
        "retell_call_id": "retell-dup",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(minutes=1)).isoformat(),
        "caller": {"phone": "+12105550101"},
    }
    first = client.post("/api/webhooks/retell/call-ended", json=payload)
    second = client.post("/api/webhooks/retell/call-ended", json=payload)
    assert first.status_code == 200
    assert second.json()["duplicate"] is True


def test_retell_webhook_legacy_hmac_in_mock_mode(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    payload = {
        "business_id": business["id"],
        "retell_call_id": "signed-call",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(seconds=10)).isoformat(),
        "caller": {"phone": "+12105550102"},
    }
    import json

    raw = json.dumps(payload).encode()
    signature = legacy_hmac_signature(raw, "test-webhook-secret")
    response = client.post(
        "/api/webhooks/retell/call-ended",
        content=raw,
        headers={"X-Retell-Signature": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200


def test_retell_connection_test_mock(client, business_with_agent):
    _, headers = business_with_agent
    response = client.post("/api/integrations/retell/test", headers=headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_cross_tenant_retell_tool_denied(client, business_with_agent):
    business, _ = business_with_agent
    other = client.post("/api/businesses", json={"name": "Other"}).json()
    start = datetime.now(UTC)
    denied = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "unknown-agent",
            "start": start.isoformat(),
            "end": (start + timedelta(days=1)).isoformat(),
        },
    )
    assert denied.status_code == 404
    assert other["id"] != business["id"]
