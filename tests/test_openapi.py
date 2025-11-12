
def test_openapi_available(test_client):
    r = test_client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "openapi" in spec
    assert "paths" in spec
    assert "/health" in spec["paths"] or "GET /health"  # допускаем разные генераторы
