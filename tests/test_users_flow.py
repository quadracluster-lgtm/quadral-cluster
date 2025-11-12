import uuid


def test_create_user_happy_path(test_client):
    payload = {
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "username": "test-user",
        "profile": {},
    }
    r = test_client.post("/users", json=payload)
    assert r.status_code in (200, 201)
