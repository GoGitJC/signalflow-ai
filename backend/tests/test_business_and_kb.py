def create_business(client, name="Alamo Dental"):
    response = client.post("/api/businesses", json={"name": name, "industry": "dental"})
    assert response.status_code == 201
    return response.json()


def test_business_and_knowledge_base_crud(client):
    business = create_business(client)
    entry = client.post(
        f"/api/businesses/{business['id']}/knowledge-base",
        json={
            "category": "hours",
            "question": "When are you open?",
            "answer": "Monday through Friday.",
        },
    )
    assert entry.status_code == 201
    entry_id = entry.json()["id"]

    listed = client.get(f"/api/businesses/{business['id']}/knowledge-base")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(f"/api/knowledge-base/{entry_id}", json={"active": False})
    assert updated.status_code == 200
    assert updated.json()["active"] is False

    deleted = client.delete(f"/api/knowledge-base/{entry_id}")
    assert deleted.status_code == 204
