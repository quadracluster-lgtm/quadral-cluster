import uuid
from copy import deepcopy


def _guess_value_for(field_name: str):
    # заготовки «разумных» значений
    if "email" in field_name:
        return f"test-{uuid.uuid4().hex[:8]}@example.com"
    if "name" in field_name or "username" in field_name:
        return "Test User"
    if "socionics_type" in field_name or field_name == "tim":
        return "IEE"  # валидный TIM
    if "idempotency" in field_name:
        return str(uuid.uuid4())
    if "password" in field_name:
        return "testPass123!"
    if "bio" in field_name:
        return "Just checking"
    if "phone" in field_name:
        return "+10000000000"
    if "age" in field_name:
        return 25
    # дефолтная подстановка
    return "test"


def _resolve_schema(spec, schema):
    # разрешение $ref до реальной схемы
    if "$ref" in schema:
        ref = schema["$ref"]
        assert ref.startswith("#/components/schemas/")
        name = ref.split("/")[-1]
        return spec["components"]["schemas"][name]
    return schema


def _min_payload_from_schema(spec, schema):
    # строим минимальный payload, заполняя только required-поля
    schema = deepcopy(_resolve_schema(spec, schema))
    typ = schema.get("type")
    if not typ and "oneOf" in schema:
        # выбираем первую альтернативу
        return _min_payload_from_schema(spec, schema["oneOf"][0])

    if typ == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = schema.get("required", [])
        payload = {}
        for key in required:
            prop = _resolve_schema(spec, props.get(key, {}))
            ptype = prop.get("type")
            if ptype == "object" or "properties" in prop:
                payload[key] = _min_payload_from_schema(spec, prop)
            elif ptype == "array":
                items = _resolve_schema(spec, prop.get("items", {}))
                # массив из одного минимального элемента
                payload[key] = [_min_payload_from_schema(spec, items)]
            else:
                payload[key] = _guess_value_for(key)
        return payload

    if typ == "array":
        items = _resolve_schema(spec, schema.get("items", {}))
        return [_min_payload_from_schema(spec, items)]

    # примитив
    return _guess_value_for("value")


def _find_users_post_request_schema(spec):
    paths = spec.get("paths", {})
    # ищем по известным вариантам регистра пользователей
    for p in ("/users", "/api/users", "/v1/users"):
        node = paths.get(p, {})
        post = node.get("post", {}) if isinstance(node, dict) else {}
        req = post.get("requestBody", {})
        content = req.get("content", {})
        app_json = content.get("application/json", {})
        schema = app_json.get("schema")
        if schema:
            return schema
    # если не нашли — вернуть None
    return None


def test_create_user_happy_path(test_client):
    # шаг 1: читаем openapi
    spec_resp = test_client.get("/openapi.json")
    assert spec_resp.status_code == 200, spec_resp.text
    spec = spec_resp.json()

    # шаг 2: достаём схему запроса на POST /users
    schema = _find_users_post_request_schema(spec)
    assert schema is not None, "POST /users schema not found in OpenAPI"

    # шаг 3: строим минимальный валидный payload
    payload = _min_payload_from_schema(spec, schema)

    # шаг 4: делаем запрос
    r = test_client.post("/users", json=payload)

    # если всё ещё 422 — выведем тело ошибки, чтобы понять обязательные поля
    assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
