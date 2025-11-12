def test_openapi_available(test_client):
    r = test_client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    # ключевые поля спецификации
    assert "openapi" in data
    assert "paths" in data
# конец файла
