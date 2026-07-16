from datetime import UTC, datetime, timedelta


def test_e2e_mocked_call_availability_booking_dashboard(client, business_with_agent):
    business, headers = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    slot_start = start + timedelta(days=2, hours=10)

    availability = client.post(
        "/api/retell/tools/check_availability",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": slot_start.isoformat(),
            "end": (slot_start + timedelta(days=1)).isoformat(),
        },
    )
    assert availability.status_code == 200
    options = availability.json()["options"]
    assert len(options) >= 1

    booked = client.post(
        "/api/retell/tools/book_appointment",
        json={
            "retell_agent_id": "agent-universal-demo",
            "start": options[0]["start"],
            "option_id": options[0]["option_id"],
            "name": "Maria",
            "email": "maria@example.com",
            "phone": "+12105550101",
            "service": "Emergency dental exam",
            "timezone": "America/Chicago",
            "caller_confirmed": True,
        },
    )
    assert booked.status_code == 200
    booking = booked.json()
    assert booking["booked"] is True

    call_payload = {
        "event_id": "evt-e2e-1",
        "business_id": business["id"],
        "retell_call_id": "retell-e2e-1",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(minutes=5)).isoformat(),
        "transcript": "Caller confirmed emergency exam.",
        "caller": {"name": "Maria", "phone": "+12105550101", "email": "maria@example.com"},
        "intent": "book_appointment",
        "urgency": "urgent",
        "outcome": "appointment_booked",
        "requested_service": "Emergency dental exam",
        "appointment": {
            "cal_event_id": booking["cal_event_id"],
            "service": "Emergency dental exam",
            "start_time": booking["start_time"],
            "end_time": booking["end_time"],
            "status": "booked",
        },
    }
    webhook = client.post("/api/webhooks/retell/call-ended", json=call_payload)
    assert webhook.status_code == 200
    assert webhook.json()["appointment_id"]

    calls = client.get(f"/api/businesses/{business['id']}/calls", headers=headers).json()
    appointments = client.get(
        f"/api/businesses/{business['id']}/appointments", headers=headers
    ).json()
    assert len(calls) == 1
    assert len(appointments) == 1
    assert calls[0]["appointment_booked"] is True
    assert appointments[0]["cal_event_id"] == booking["cal_event_id"]

    retell_status = client.get("/api/integrations/retell/status", headers=headers)
    calcom_status = client.get("/api/integrations/calcom/status", headers=headers)
    assert retell_status.status_code == 200
    assert calcom_status.status_code == 200
