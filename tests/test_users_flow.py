import uuid


def test_create_user_happy_path(test_client):
    payload = {
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "socionics_type": "IEE",
        # если эндпоинт требует идемпотентность — раскомментируй строку ниже:
        # "idempotency_key": str(uuid.uuid4()),
    }
    r = test_client.post("/users", json=payload)
    assert r.status_code in (200, 201)
