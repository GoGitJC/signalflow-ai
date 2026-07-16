from datetime import UTC, datetime, timedelta

from tests.conftest import create_business


def test_callers_crm_and_analytics_and_voice_agent(client, business_with_agent):
    business, headers = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)

    ended = client.post(
        "/api/webhooks/retell/call-ended",
        json={
            "event_id": "crm-evt-1",
            "business_id": business["id"],
            "retell_call_id": "crm-call-1",
            "started_at": start.isoformat(),
            "ended_at": (start + timedelta(minutes=3)).isoformat(),
            "transcript": "I need a cleaning next week.",
            "caller": {"name": "Alex Rivera", "phone": "+12105550123", "email": "alex@example.com"},
            "intent": "book_appointment",
            "outcome": "appointment_booked",
            "sentiment": "positive",
            "appointment": {
                "service": "Cleaning",
                "start_time": (start + timedelta(days=2)).isoformat(),
                "end_time": (start + timedelta(days=2, hours=1)).isoformat(),
                "status": "booked",
            },
        },
    )
    assert ended.status_code == 200
    call = ended.json()["call"]
    assert call["sentiment"] == "positive"
    caller_id = call["caller_id"]

    listed = client.get(f"/api/businesses/{business['id']}/callers", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["call_count"] == 1
    assert listed.json()[0]["appointment_count"] == 1

    patched = client.patch(
        f"/api/callers/{caller_id}",
        headers=headers,
        json={"notes": "VIP referral", "tags": ["vip", "cleaning"], "status": "customer"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "customer"
    assert "vip" in patched.json()["tags"]

    analytics = client.get(
        f"/api/businesses/{business['id']}/analytics/summary?range=7d",
        headers=headers,
    )
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["calls_total"] >= 1
    assert body["bookings"] >= 1
    assert body["series"]

    agents = client.get(f"/api/businesses/{business['id']}/voice-agents", headers=headers)
    assert agents.status_code == 200
    assert len(agents.json()) == 1
    agent_id = agents.json()[0]["id"]

    updated = client.patch(
        f"/api/voice-agents/{agent_id}",
        headers=headers,
        json={"greeting": "Hello, Alamo Dental", "transfer_number": "+12105550999"},
    )
    assert updated.status_code == 200
    assert updated.json()["greeting"] == "Hello, Alamo Dental"

    kb = client.post(
        f"/api/businesses/{business['id']}/knowledge-base",
        headers=headers,
        json={"category": "hours", "question": "Hours?", "answer": "Mon-Fri"},
    )
    assert kb.status_code == 201
    entry_id = kb.json()["id"]
    client.patch(
        f"/api/knowledge-base/{entry_id}",
        headers=headers,
        json={"answer": "Mon-Sat"},
    )
    versions = client.get(f"/api/knowledge-base/{entry_id}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()) >= 2

    bulk = client.post(
        f"/api/businesses/{business['id']}/knowledge-base/bulk",
        headers=headers,
        json={
            "entries": [
                {"category": "pricing", "question": "Cost?", "answer": "Starts at $99"},
            ]
        },
    )
    assert bulk.status_code == 201
    assert bulk.json()["created"] == 1

    audit = client.get(f"/api/businesses/{business['id']}/audit-events", headers=headers)
    assert audit.status_code == 200


def test_create_business_still_requires_owner_token(client):
    denied = client.post("/api/businesses", json={"name": "No Auth"})
    assert denied.status_code == 401
    ok = create_business(client, name="Bootstrap Biz")
    assert ok["id"]
