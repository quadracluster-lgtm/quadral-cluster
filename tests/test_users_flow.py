from fastapi.testclient import TestClient


def test_create_user_flow(client: TestClient) -> None:
    payload = {
        "email": "user@example.com",
        "username": "example",
        "profile": {},
    }

    response = client.post("/users", json=payload)

    assert response.status_code in {200, 201}

    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]
