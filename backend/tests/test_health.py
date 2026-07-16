def test_health_live_ready_and_metrics(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers.get("x-request-id")

    live = client.get("/live")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"]["database"] == "ok"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "text/plain" in metrics.headers["content-type"]


def test_error_schema_includes_request_id(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    body = response.json()
    assert body["detail"]
    assert body["error"]["code"]
    assert body["error"]["message"]
    assert body["error"]["request_id"]
