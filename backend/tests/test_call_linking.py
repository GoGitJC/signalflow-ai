"""Retell call record ↔ appointment linkage."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.core.config import Settings
from tests.conftest import retell_signature, tenant_headers


def test_signed_call_started_creates_call_record(client, business_with_agent):
    business, _ = business_with_agent
    api_key = "retell-live-test-key"
    live_settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        integration_mode="live",
        mock_external_services=False,
        allow_live_booking=False,
        retell_api_key=api_key,
        owner_api_token="test-owner-token",
    )

    start_ms = int(datetime.now(UTC).timestamp() * 1000)
    payload = {
        "event": "call_started",
        "call": {
            "call_id": "signed-started-1",
            "agent_id": "agent-universal-demo",
            "direction": "inbound",
            "start_timestamp": start_ms,
            "from_number": "+12105550199",
        },
    }
    raw = json.dumps(payload, separators=(",", ":"))

    raw_bytes = raw.encode("utf-8")
    with (
        patch("app.api.routes.webhooks.settings", live_settings),
        patch(
            "app.api.routes.webhooks.load_retell_credentials",
            return_value={"api_key": api_key},
        ),
    ):
        missing = client.post(
            "/api/webhooks/retell",
            content=raw_bytes,
            headers={"Content-Type": "application/json"},
        )
        assert missing.status_code == 401

        response = client.post(
            "/api/webhooks/retell",
            content=raw_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Retell-Signature": retell_signature(raw, api_key),
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "processed"
        assert body["call"]["retell_call_id"] == "signed-started-1"
        assert body["call"]["business_id"] == business["id"]

        duplicate = client.post(
            "/api/webhooks/retell",
            content=raw_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Retell-Signature": retell_signature(raw, api_key),
            },
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["duplicate"] is True
        assert duplicate.json()["status"] == "already_processed"


def test_book_appointment_resolves_call_by_retell_id_and_sets_call_id(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    created = client.post(
        "/api/webhooks/retell/call-started",
        json={
            "business_id": business["id"],
            "retell_call_id": "link-by-retell-id",
            "started_at": start.isoformat(),
        },
    )
    assert created.status_code == 200
    call = created.json()["call"]

    avail = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": (start + timedelta(days=2)).isoformat(),
            "end": (start + timedelta(days=3)).isoformat(),
        },
    ).json()
    option = avail["options"][0]

    booked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "name": "book_appointment",
            "call": {
                "call_id": "link-by-retell-id",
                "agent_id": "agent-universal-demo",
            },
            "args": {
                "start": option["start"],
                "option_id": option["option_id"],
                "name": "Link Test",
                "email": "link@example.com",
                "phone": "+12105550133",
                "service": "Exam",
                "caller_confirmed": True,
            },
        },
    )
    assert booked.status_code == 200
    assert booked.json()["booked"] is True

    headers = tenant_headers(business["id"])
    appointments = client.get(
        f"/api/businesses/{business['id']}/appointments", headers=headers
    ).json()
    assert len(appointments) == 1
    assert appointments[0]["call_id"] == call["id"]
    assert appointments[0]["call_id"] is not None


def test_book_appointment_creates_stub_call_for_unknown_retell_id(client, business_with_agent):
    """If webhook has not arrived yet, booking still links via a stub Call row."""
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    avail = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": (start + timedelta(days=4)).isoformat(),
            "end": (start + timedelta(days=5)).isoformat(),
        },
    ).json()
    option = avail["options"][0]

    booked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "name": "book_appointment",
            "call": {"call_id": "unknown-but-real-call", "agent_id": "agent-universal-demo"},
            "args": {
                "start": option["start"],
                "option_id": option["option_id"],
                "name": "Race Caller",
                "email": "race@example.com",
                "phone": "+12105550144",
                "service": "Exam",
                "caller_confirmed": True,
            },
        },
    )
    assert booked.status_code == 200
    assert booked.json()["booked"] is True

    headers = tenant_headers(business["id"])
    appointments = client.get(
        f"/api/businesses/{business['id']}/appointments", headers=headers
    ).json()
    assert len(appointments) == 1
    assert appointments[0]["call_id"] is not None

    call = client.get(
        f"/api/calls/{appointments[0]['call_id']}",
        params={"business_id": business["id"]},
        headers=headers,
    ).json()
    assert call["retell_call_id"] == "unknown-but-real-call"
    assert call["appointment_booked"] is True

    # Later call_started for same Retell ID reuses the stub (idempotent).
    started = client.post(
        "/api/webhooks/retell/call-started",
        json={
            "business_id": business["id"],
            "retell_call_id": "unknown-but-real-call",
            "started_at": start.isoformat(),
        },
    )
    assert started.status_code == 200
    assert started.json()["call"]["id"] == appointments[0]["call_id"]


def test_book_without_retell_call_id_leaves_call_id_null(client, business_with_agent):
    business, _ = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    avail = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": (start + timedelta(days=6)).isoformat(),
            "end": (start + timedelta(days=7)).isoformat(),
        },
    ).json()
    option = avail["options"][0]

    booked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": option["start"],
            "option_id": option["option_id"],
            "name": "No Link",
            "email": "nolink@example.com",
            "phone": "+12105550155",
            "service": "Exam",
            "caller_confirmed": True,
        },
    )
    assert booked.status_code == 200
    headers = tenant_headers(business["id"])
    appointments = client.get(
        f"/api/businesses/{business['id']}/appointments", headers=headers
    ).json()
    assert appointments[0]["call_id"] is None
