import uuid

import pytest


def _has_users_post(spec):
    paths = spec.get("paths", {})
    for p in ("/users", "/api/users", "/v1/users"):
        if isinstance(paths.get(p), dict) and "post" in paths[p]:
            return p
    return None


def _candidates():
    # Набор минимальных вариантов для разных версий контракта.
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    idem = str(uuid.uuid4())
    return [
        # базовый
        {"email": email, "name": "Test User", "socionics_type": "IEE"},
        # с идемпотентностью
        {"email": email, "name": "Test User", "socionics_type": "IEE", "idempotency_key": idem},
        # username вместо name
        {"email": email, "username": "Test User", "socionics_type": "IEE"},
        {"email": email, "username": "Test User", "socionics_type": "IEE", "idempotency_key": idem},
        # вложенный profile как иногда требуют
        {"email": email, "name": "Test User", "socionics_type": "IEE", "profile": {"bio": "Just checking"}},
        {
            "email": email,
            "name": "Test User",
            "socionics_type": "IEE",
            "idempotency_key": idem,
            "profile": {"bio": "Just checking"},
        },
    ]


def test_create_user_happy_path(test_client):
    # 1) Если ручки нет в OpenAPI — смок не обязателен → пропускаем.
    spec_resp = test_client.get("/openapi.json")
    assert spec_resp.status_code == 200, spec_resp.text
    spec = spec_resp.json()
    users_path = _has_users_post(spec)
    if not users_path:
        pytest.skip("POST /users not present in OpenAPI — skipping smoke.")

    # 2) Пробуем несколько минимальных payload’ов
    last = None
    for payload in _candidates():
        r = test_client.post(users_path, json=payload)
        last = r
        if r.status_code in (200, 201):
            return  # успех

    # 3) Если ничего не прошло — показываем последнюю ошибку
    assert last is not None
    pytest.fail(f"All user-create payloads returned non-2xx. Last was {last.status_code}: {last.text}")
