from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import httpx
import pytest

from app.integrations.calcom_client import CalComClient
from app.integrations.errors import (
    ProviderAuthError,
    ProviderConflictError,
    ProviderRateLimitError,
)
from app.schemas.integration import AvailabilityRequest, BookingRequest


def test_calcom_connection_test_mock(client, business_with_agent):
    _, headers = business_with_agent
    response = client.post("/api/integrations/calcom/test", headers=headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_calcom_resolve_event_type_by_id():
    client = CalComClient("key", event_type_id="123")
    payload = {"data": {"id": 123, "slug": "consult", "title": "Consultation"}}
    with patch("app.integrations.calcom_client.request_json", return_value=payload):
        resolved = client.resolve_event_type()
    assert resolved["event_type_id"] == "123"
    assert resolved["slug"] == "consult"


def test_calcom_resolve_event_type_slug_ambiguous():
    client = CalComClient("key", event_type_slug="consult", username="demo")
    payload = {"data": [{"id": 1, "slug": "consult"}, {"id": 2, "slug": "consult"}]}
    with patch("app.integrations.calcom_client.request_json", return_value=payload):
        with pytest.raises(ProviderConflictError):
            client.resolve_event_type()


def test_calcom_slots_retrieval():
    client = CalComClient("key", event_type_id="10")
    request = AvailabilityRequest(
        business_id="biz",
        event_type_id="10",
        start=datetime(2026, 7, 16, tzinfo=UTC),
        end=datetime(2026, 7, 17, tzinfo=UTC),
    )
    payload = {"data": {"2026-07-16": ["2026-07-16T14:00:00Z"]}}
    with patch("app.integrations.calcom_client.request_json", return_value=payload):
        with patch.object(
            client,
            "resolve_event_type",
            return_value={"event_type_id": "10", "slug": "s", "username": "u"},
        ):
            slots = client.availability(request)
    assert len(slots) == 1


def test_calcom_no_available_slots():
    client = CalComClient("key", event_type_id="10")
    request = AvailabilityRequest(
        business_id="biz",
        event_type_id="10",
        start=datetime(2026, 7, 16, tzinfo=UTC),
        end=datetime(2026, 7, 17, tzinfo=UTC),
    )
    with patch("app.integrations.calcom_client.request_json", return_value={"data": {}}):
        with patch.object(
            client,
            "resolve_event_type",
            return_value={"event_type_id": "10", "slug": "s", "username": "u"},
        ):
            slots = client.availability(request)
    assert slots == []


def test_calcom_successful_booking():
    client = CalComClient("key", event_type_id="10")
    request = BookingRequest(
        business_id="biz",
        event_type_id="10",
        start=datetime(2026, 7, 16, 14, 0, tzinfo=UTC),
        name="Maria",
        email="maria@example.com",
        phone="+12105550101",
        service="Exam",
    )
    payload = {"data": {"uid": "booking-uid-1", "status": "accepted", "lengthInMinutes": 30}}
    with patch("app.integrations.calcom_client.request_json", return_value=payload):
        with patch.object(
            client,
            "resolve_event_type",
            return_value={"event_type_id": "10", "slug": "s", "username": "u"},
        ):
            result = client.book(request, idempotency_key="idem-1")
    assert result["cal_event_id"] == "booking-uid-1"


def test_calcom_booking_conflict_maps_error():
    client = CalComClient("key", event_type_id="10")
    response = httpx.Response(409, json={"message": "conflict"})
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = response
        with pytest.raises(ProviderConflictError):
            client.resolve_event_type()


def test_calcom_rate_limit_maps_error():
    client = CalComClient("key", event_type_id="10")
    response = httpx.Response(429, json={"message": "slow down"})
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = response
        with pytest.raises(ProviderRateLimitError):
            client.resolve_event_type()


def test_calcom_invalid_api_key():
    client = CalComClient("bad", event_type_id="10")
    response = httpx.Response(401, json={"message": "Unauthorized"})
    with patch("app.integrations.http_utils.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = response
        with pytest.raises(ProviderAuthError):
            client.resolve_event_type()


def test_duplicate_booking_protection(client, business_with_agent):
    business, headers = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=2)
    payload = {
        "business_id": business["id"],
        "start": start.isoformat(),
        "name": "Maria",
        "email": "maria@example.com",
        "phone": "+12105550101",
        "service": "Exam",
    }
    first = client.post("/api/integrations/calcom/book", headers=headers, json=payload)
    second = client.post("/api/integrations/calcom/book", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True


def test_calcom_webhook_status_update(client, business_with_agent):
    business, headers = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=3)
    booked = client.post(
        "/api/integrations/calcom/book",
        headers=headers,
        json={
            "business_id": business["id"],
            "start": start.isoformat(),
            "name": "Alex",
            "email": "alex@example.com",
            "service": "Cleaning",
        },
    ).json()
    webhook = client.post(
        "/api/webhooks/calcom",
        json={"id": "evt-1", "uid": booked["cal_event_id"], "status": "cancelled"},
    )
    assert webhook.status_code == 200
    appointments = client.get(
        f"/api/businesses/{business['id']}/appointments", headers=headers
    ).json()
    assert appointments[0]["status"] == "cancelled"


def test_cross_tenant_calcom_booking_denied(client, business_with_agent):
    from tests.conftest import create_business, tenant_headers

    business, headers = business_with_agent
    other = create_business(client, name="Other Biz")
    start = datetime.now(UTC) + timedelta(days=4)
    booked = client.post(
        "/api/integrations/calcom/book",
        headers=headers,
        json={
            "business_id": business["id"],
            "start": start.isoformat(),
            "name": "Pat",
            "email": "pat@example.com",
            "service": "Exam",
        },
    ).json()
    appointments = client.get(
        f"/api/businesses/{other['id']}/appointments",
        headers=tenant_headers(other["id"]),
    ).json()
    assert all(item["id"] != booked["appointment_id"] for item in appointments)
