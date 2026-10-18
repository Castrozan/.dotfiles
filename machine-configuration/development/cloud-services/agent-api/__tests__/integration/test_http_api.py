import uuid

from fastapi.testclient import TestClient

from agent_api.transport import create_app


def test_openapi_discovery_and_schema_are_available_without_provider_credentials(
    tmp_path,
):
    client = TestClient(create_app(tmp_path / "state"))
    assert client.get("/openapi.json").status_code == 200
    entries = client.get("/v1/capabilities", params={"query": "transcribe"}).json()[
        "capabilities"
    ]
    assert [entry["id"] for entry in entries] == ["audio.transcribe"]
    assert "input_schema" not in entries[0]
    assert client.get("/v1/capabilities/audio.transcribe").json()["input_schema"][
        "required"
    ] == ["path", "model_path"]


def test_http_validation_rejects_unknown_and_paid_requests_without_dispatch(tmp_path):
    client = TestClient(create_app(tmp_path / "state"))
    operation_id = str(uuid.uuid4())
    response = client.put(
        "/v1/operations/" + operation_id,
        json={
            "capability": "web.extract",
            "input": {"url": "https://example.com"},
            "extra": True,
        },
    )
    assert response.status_code == 422
    response = client.put(
        "/v1/operations/" + operation_id,
        json={
            "capability": "fal.run",
            "input": {"endpoint": "fal-ai/flux/schnell", "input": {}},
        },
    )
    assert response.status_code == 422
    assert response.json()["error"] == "payment_permission_required"
    assert client.get("/v1/operations/" + operation_id).status_code == 404


def test_http_request_size_is_bounded_before_parsing(tmp_path):
    client = TestClient(create_app(tmp_path / "state"))
    response = client.put(
        "/v1/operations/" + str(uuid.uuid4()), content=b"x" * (64 * 1024 + 1)
    )
    assert response.status_code == 413
