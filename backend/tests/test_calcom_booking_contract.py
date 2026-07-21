from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.integrations.calcom_client import CalComClient
from app.integrations.errors import (
    ProviderAuthError,
    ProviderConflictError,
    ProviderError,
    ProviderRateLimitError,
    ProviderValidationError,
)
from app.schemas.integration import BookingRequest, unwrap_retell_tool_payload
from app.services.appointments import book_appointment_transactional


def _booking_request(**overrides):
    base = {
        "business_id": "biz-1",
        "event_type_id": "123",
        "start": datetime.now(UTC) + timedelta(days=2),
        "name": "Jordan Blake",
        "email": "jordan.blake@customers.forgelinq.dev",
        "phone": "+15125550111",
        "service": "AC diagnostic",
        "timezone": "America/Chicago",
    }
    base.update(overrides)
    return BookingRequest(**base)


def test_calcom_book_payload_contract():
    client = CalComClient("key", event_type_id="42")
    request = _booking_request(event_type_id="42")
    captured: dict = {}

    def fake_request_json(settings, **kwargs):
        captured.update(kwargs)
        if kwargs["method"] == "GET":
            return {"data": {"id": 42, "slug": "consult", "title": "Consult"}}
        return {
            "status": "success",
            "data": {"uid": "cal-uid-1", "status": "accepted", "lengthInMinutes": 30},
        }

    with patch("app.integrations.calcom_client.request_json", side_effect=fake_request_json):
        result = client.book(request, idempotency_key="abc")

    assert captured["method"] == "POST"
    assert captured["url"].endswith("/bookings")
    assert captured["headers"]["cal-api-version"] == "2024-08-13"
    body = captured["json_body"]
    assert body["eventTypeId"] == 42
    assert body["attendee"]["language"] == "en"
    assert body["attendee"]["phoneNumber"] == "+15125550111"
    assert body["start"].endswith("Z")
    assert "eventTypeSlug" not in body
    assert result["cal_event_id"] == "cal-uid-1"


@pytest.mark.parametrize(
    ("exc",),
    [
        (ProviderValidationError("bad email"),),
        (ProviderAuthError("nope"),),
        (ProviderConflictError("taken"),),
        (ProviderRateLimitError("slow"),),
        (ProviderError("server", status_code=500, retryable=True),),
    ],
)
def test_calcom_book_provider_errors_propagate(exc):
    client = CalComClient("key", event_type_id="42")
    request = _booking_request()
    with patch.object(client, "resolve_event_type", return_value={"event_type_id": "42"}):
        with patch("app.integrations.calcom_client.request_json", side_effect=exc):
            with pytest.raises(type(exc)):
                client.book(request)


def test_unwrap_rejects_envelope_without_args():
    with pytest.raises(ValueError, match="missing args"):
        unwrap_retell_tool_payload({"name": "book_appointment", "call": {"call_id": "c1"}})


def test_unwrap_accepts_args_only_and_envelope():
    flat = unwrap_retell_tool_payload(
        {
            "retell_agent_id": "agent-1",
            "start": "2026-07-21T15:00:00Z",
            "name": "Pat",
            "email": "pat@customers.forgelinq.dev",
            "service": "Exam",
            "caller_confirmed": True,
        }
    )
    assert flat["retell_agent_id"] == "agent-1"

    env = unwrap_retell_tool_payload(
        {
            "name": "book_appointment",
            "call": {"call_id": "c1", "agent_id": "agent-1"},
            "args": {
                "start": "2026-07-21T15:00:00Z",
                "name": "Pat",
                "email": "pat@customers.forgelinq.dev",
                "service": "Exam",
                "caller_confirmed": True,
            },
        }
    )
    assert env["retell_agent_id"] == "agent-1"
    assert env["retell_call_id"] == "c1"


def test_placeholder_email_rejected_in_live_mode(db, monkeypatch):
    monkeypatch.setenv("INTEGRATION_MODE", "live")
    monkeypatch.setenv("SIGNALFLOW_MOCK_EXTERNAL_SERVICES", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    request = _booking_request(email="mail@example.com", business_id="biz")
    try:
        with pytest.raises(HTTPException) as exc:
            book_appointment_transactional(db, request, allow_live=True)
        assert exc.value.status_code == 422
    finally:
        get_settings.cache_clear()


def test_provider_success_duplicate_local_does_not_rebook(db, business_with_agent):
    business, _ = business_with_agent
    start = (datetime.now(UTC) + timedelta(days=4)).replace(microsecond=0)
    request = _booking_request(
        business_id=business["id"],
        start=start,
        email="real.person@customers.forgelinq.dev",
    )

    provider = MagicMock()
    provider.book.return_value = {
        "cal_event_id": "uid-stable-1",
        "start_time": start,
        "end_time": start + timedelta(minutes=30),
        "status": "booked",
    }
    with patch("app.services.appointments.get_scheduling_for_business", return_value=provider):
        first, _ = book_appointment_transactional(db, request, allow_live=True)
        second, meta2 = book_appointment_transactional(db, request, allow_live=True)

    assert first.id == second.id
    assert meta2["duplicate"] is True
    assert provider.book.call_count == 1
