from tests.conftest import create_business, tenant_headers


def test_business_and_knowledge_base_crud(client):
    business = create_business(client)
    headers = tenant_headers(business["id"])

    entry = client.post(
        f"/api/businesses/{business['id']}/knowledge-base",
        json={
            "category": "hours",
            "question": "When are you open?",
            "answer": "Monday through Friday.",
        },
        headers=headers,
    )
    assert entry.status_code == 201
    entry_id = entry.json()["id"]

    listed = client.get(f"/api/businesses/{business['id']}/knowledge-base", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/knowledge-base/{entry_id}",
        json={"active": False},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is False

    deleted = client.delete(f"/api/knowledge-base/{entry_id}", headers=headers)
    assert deleted.status_code == 204


def test_tenant_routes_require_auth(client):
    business = create_business(client)
    denied = client.get(f"/api/businesses/{business['id']}/calls")
    assert denied.status_code == 401
