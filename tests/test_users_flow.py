from fastapi.testclient import TestClient
from src.quadral_cluster.main import app

client = TestClient(app)

def test_create_user_201_and_echo_fields():
    payload = {
        "telegram_id": 11111,
        "username": "demo_user",
        "email": "demo@example.com",
        "profile": {
            "age": 26,
            "bio": "Тестовый пользователь для Quadral Cluster",
            "city": "Москва",
            "timezone": "Europe/Moscow",
            "interests": ["IT", "Psychology"],
            "socionics_type": "ILE",
            "psychotype": "ENFP",
            "reputation_score": 0.7,
            "activity_score": 0.8
        }
    }
    r = client.post("/users", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["username"] == payload["username"]
    assert body["profile"]["city"] == payload["profile"]["city"]
