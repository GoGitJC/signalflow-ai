from datetime import UTC, datetime, timedelta


def test_mock_availability_and_sms(client, business_with_agent):
    business, headers = business_with_agent
    start = datetime.now(UTC).replace(microsecond=0)
    availability = client.post(
        "/api/integrations/calcom/availability",
        headers=headers,
        json={
            "business_id": business["id"],
            "event_type_id": "30-min",
            "start": start.isoformat(),
            "end": (start + timedelta(hours=3)).isoformat(),
        },
    )
    assert availability.status_code == 200
    assert availability.json()["mocked"] is True
    assert len(availability.json()["slots"]) == 3

    sms = client.post(
        "/api/integrations/twilio/send-summary",
        json={"business_id": business["id"], "to": "+12105550100", "message": "New qualified lead"},
    )
    assert sms.status_code == 200
    assert sms.json()["status"] == "queued"
