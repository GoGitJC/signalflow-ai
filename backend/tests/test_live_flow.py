from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.integrations.errors import ProviderConflictError, ProviderTimeoutError
from app.integrations.retell_signature import verify_retell_signature
from tests.conftest import retell_signature


def test_agent_to_business_mapping_and_cross_tenant_denial(client, business_with_agent):
    business, _ = business_with_agent
    other = client.post("/api/businesses", json={"name": "Other"}).json()
    start = datetime.now(UTC) + timedelta(days=5)
    ok = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": start.isoformat(),
            "end": (start + timedelta(days=1)).isoformat(),
            "timezone": "America/Chicago",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["available"] is True
    assert ok.json()["options"]

    denied = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-other-business",
            "start": start.isoformat(),
            "end": (start + timedelta(days=1)).isoformat(),
        },
    )
    assert denied.status_code == 404
    assert other["id"] != business["id"]


def test_voice_tool_booking_requires_confirmation_and_links_call(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    call = client.post(
        "/api/webhooks/retell/call-started",
        json={
            "business_id": business["id"],
            "retell_call_id": "tool-link-call",
            "started_at": start.isoformat(),
        },
    ).json()["call"]

    avail = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": (start + timedelta(days=3)).isoformat(),
            "end": (start + timedelta(days=4)).isoformat(),
        },
    ).json()
    option = avail["options"][0]

    blocked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": option["start"],
            "option_id": option["option_id"],
            "name": "Maria",
            "email": "maria@example.com",
            "phone": "+12105550111",
            "service": "Exam",
            "caller_confirmed": False,
            "retell_call_id": "tool-link-call",
        },
    )
    assert blocked.status_code == 200
    assert blocked.json()["requires_confirmation"] is True
    assert blocked.json()["booked"] is False

    booked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": option["start"],
            "option_id": option["option_id"],
            "name": "Maria",
            "email": "maria@example.com",
            "phone": "+12105550111",
            "service": "Exam",
            "caller_confirmed": True,
            "retell_call_id": "tool-link-call",
        },
    )
    assert booked.status_code == 200
    body = booked.json()
    assert body["booked"] is True
    assert body["appointment_id"]

    appointments = client.get(f"/api/businesses/{business['id']}/appointments").json()
    assert len(appointments) == 1
    assert appointments[0]["id"] == body["appointment_id"]
    assert appointments[0]["call_id"] == call["id"]

    call_detail = client.get(
        f"/api/calls/{call['id']}", params={"business_id": business["id"]}
    ).json()
    assert call_detail["appointment_booked"] is True


def test_no_availability_voice_response(client, business_with_agent):
    _, _ = business_with_agent
    start = datetime.now(UTC) + timedelta(days=8)
    with patch("app.api.routes.retell_tools.get_scheduling_for_business") as mock_provider:
        mock_provider.return_value.availability.return_value = []
        response = client.post(
            "/api/retell/tools/check_availability",
            json={
                "retell_agent_id": "agent-universal-demo",
                "start": start.isoformat(),
                "end": (start + timedelta(days=1)).isoformat(),
            },
        )
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["options"] == []


def test_calcom_availability_success_and_invalid_event_type(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC) + timedelta(days=9)
    ok = client.post(
        "/api/integrations/calcom/availability",
        json={
            "business_id": business["id"],
            "start": start.isoformat(),
            "end": (start + timedelta(days=1)).isoformat(),
        },
    )
    assert ok.status_code == 200
    assert len(ok.json()["slots"]) > 0

    from app.integrations.calcom_client import CalComClient
    from app.integrations.errors import ProviderNotFoundError

    with patch("app.integrations.calcom_client.request_json", return_value={"data": []}):
        with pytest.raises(ProviderNotFoundError):
            CalComClient("key", event_type_slug="missing", username="demo").resolve_event_type()


def test_booking_conflict_and_duplicate(client, business_with_agent):
    business, _ = business_with_agent
    start = (datetime.now(UTC) + timedelta(days=10)).replace(microsecond=0)
    payload = {
        "business_id": business["id"],
        "start": start.isoformat(),
        "name": "Pat",
        "email": "pat@example.com",
        "service": "Cleaning",
    }
    first = client.post("/api/integrations/calcom/book", json=payload)
    second = client.post("/api/integrations/calcom/book", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    with patch("app.services.appointments.get_scheduling_for_business") as mock_provider:
        mock_provider.return_value.book.side_effect = ProviderConflictError("taken")
        conflict = client.post(
            "/api/integrations/calcom/book",
            json={**payload, "start": (start + timedelta(hours=2)).isoformat()},
        )
    assert conflict.status_code == 409


def test_provider_timeout_maps_and_invalid_signature(monkeypatch):
    with pytest.raises(HTTPException):
        verify_retell_signature("{}", None, "key")
    with pytest.raises(HTTPException):
        verify_retell_signature("{}", "v=1,d=deadbeef", "key")

    body = '{"event":"call_ended"}'
    sig = retell_signature(body, "good-key")
    verify_retell_signature(body, sig, "good-key")

    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        import httpx

        from app.integrations.retell_client import RetellClient

        mock_client.return_value.__enter__.return_value.request.side_effect = (
            httpx.TimeoutException("timeout")
        )
        with pytest.raises(ProviderTimeoutError):
            RetellClient("key").list_agents()


def test_duplicate_webhook_and_cross_tenant_call_read(client, business_with_agent):
    business, _ = business_with_agent
    other = client.post("/api/businesses", json={"name": "Tenant B"}).json()
    start = datetime.now(UTC).replace(microsecond=0)
    payload = {
        "event_id": "dup-webhook-1",
        "business_id": business["id"],
        "retell_call_id": "dup-call-1",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(minutes=1)).isoformat(),
        "caller": {"phone": "+12105550999"},
    }
    first = client.post("/api/webhooks/retell/call-ended", json=payload)
    second = client.post("/api/webhooks/retell/call-ended", json=payload)
    assert first.status_code == 200
    assert second.json()["duplicate"] is True
    call_id = first.json()["call"]["id"]
    denied = client.get(f"/api/calls/{call_id}", params={"business_id": other["id"]})
    assert denied.status_code == 404


def test_connection_tests_persist_status(client, business_with_agent):
    _, headers = business_with_agent
    retell = client.post("/api/integrations/retell/test", headers=headers)
    calcom = client.post("/api/integrations/calcom/test", headers=headers)
    assert retell.status_code == 200
    assert calcom.status_code == 200
    status = client.get("/api/integrations/retell/status", headers=headers)
    assert status.json()["last_test_status"] == "ok"
    assert status.json()["agent_name"]
