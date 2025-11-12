def test_health_ok(test_client):
    r = test_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("status") == "ok"
