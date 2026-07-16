def test_exports_and_readiness(client, business_with_agent):
    business, headers = business_with_agent
    business_id = business["id"]

    customers = client.get(f"/api/businesses/{business_id}/exports/customers.csv", headers=headers)
    assert customers.status_code == 200
    assert "text/csv" in customers.headers["content-type"]
    assert "id,name,phone" in customers.text.splitlines()[0]

    appointments = client.get(
        f"/api/businesses/{business_id}/exports/appointments.csv", headers=headers
    )
    assert appointments.status_code == 200
    assert "service" in appointments.text.splitlines()[0]

    calls = client.get(f"/api/businesses/{business_id}/exports/calls.csv", headers=headers)
    assert calls.status_code == 200
    assert "retell_call_id" in calls.text.splitlines()[0]

    readiness = client.get(f"/api/businesses/{business_id}/readiness", headers=headers)
    assert readiness.status_code == 200
    body = readiness.json()
    assert "score" in body
    assert isinstance(body["checks"], list)
    assert body["allow_live_booking"] is False


def test_audit_search_query_param(client, business_with_agent):
    business, headers = business_with_agent
    response = client.get(
        f"/api/businesses/{business['id']}/audit-events",
        params={"q": "login", "limit": 10},
        headers=headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
