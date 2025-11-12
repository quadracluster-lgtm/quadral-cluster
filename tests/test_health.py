
def test_health_ok(test_client):
    r = test_client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
