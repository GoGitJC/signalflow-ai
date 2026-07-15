from datetime import UTC, datetime, timedelta


def test_completed_call_webhook_creates_caller_call_summary_and_appointment(client):
    business = client.post("/api/businesses", json={"name": "Alamo Dental"}).json()
    start = datetime.now(UTC).replace(microsecond=0)
    payload = {
        "event_id": "evt-call-ended-1",
        "business_id": business["id"],
        "retell_call_id": "retell-call-100",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(minutes=4)).isoformat(),
        "transcript": "Caller needs an emergency exam tomorrow morning.",
        "caller": {"name": "Maria", "phone": "+12105550101", "email": "maria@example.com"},
        "intent": "book_appointment",
        "urgency": "urgent",
        "outcome": "appointment_booked",
        "requested_service": "Emergency dental exam",
        "appointment": {
            "cal_event_id": "cal-100",
            "service": "Emergency dental exam",
            "start_time": (start + timedelta(days=1)).isoformat(),
            "end_time": (start + timedelta(days=1, minutes=30)).isoformat(),
            "status": "booked",
        },
    }
    response = client.post("/api/webhooks/retell/call-ended", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["call"]["duration_seconds"] == 240
    assert body["call"]["appointment_booked"] is True
    assert "Emergency dental exam" in body["call"]["summary"]
    assert body["appointment_id"]

    calls = client.get(f"/api/businesses/{business['id']}/calls").json()
    appointments = client.get(f"/api/businesses/{business['id']}/appointments").json()
    assert len(calls) == 1
    assert len(appointments) == 1

    duplicate = client.post("/api/webhooks/retell/call-ended", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert len(client.get(f"/api/businesses/{business['id']}/calls").json()) == 1


def test_call_detail_is_tenant_scoped(client):
    first = client.post("/api/businesses", json={"name": "First"}).json()
    second = client.post("/api/businesses", json={"name": "Second"}).json()
    start = datetime.now(UTC).replace(microsecond=0)
    payload = {
        "business_id": first["id"],
        "retell_call_id": "tenant-call",
        "started_at": start.isoformat(),
        "ended_at": (start + timedelta(seconds=30)).isoformat(),
        "caller": {"phone": "+12105550000"},
    }
    call = client.post("/api/webhooks/retell/call-ended", json=payload).json()["call"]
    denied = client.get(f"/api/calls/{call['id']}", params={"business_id": second["id"]})
    assert denied.status_code == 404
