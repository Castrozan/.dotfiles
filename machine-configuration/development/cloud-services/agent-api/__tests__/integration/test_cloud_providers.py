import json

import httpx
import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.providers.cloud import CloudProvider
from agent_api.providers.network import NetworkClient


def client_for(handler):
    return NetworkClient(10, httpx.Client(transport=httpx.MockTransport(handler)))


def test_monid_async_run_submits_once_and_retains_remote_identity(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MONID_API_KEY", "synthetic")
    calls = []

    def respond(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer synthetic"
        if request.method == "POST":
            return httpx.Response(202, json={"runId": "remote-id", "status": "RUNNING"})
        return httpx.Response(
            200,
            json={
                "runId": "remote-id",
                "status": "COMPLETED",
                "providerResponse": {"httpStatus": 200},
                "output": {"text": "result"},
            },
        )

    client = client_for(respond)
    monkeypatch.setattr(client, "pause", lambda: None)
    request = OperationRequest(
        "monid.run",
        {"provider": "apify", "endpoint": "/example", "input": {}},
        allow_paid=True,
    )
    result = CloudProvider().monid(request, tmp_path, client)
    assert result["output"] == {"text": "result"}
    assert [call.method for call in calls] == ["POST", "GET"]
    assert (
        json.loads((tmp_path / "submission.json").read_text())["run_id"] == "remote-id"
    )


def test_monid_completed_provider_error_is_a_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("MONID_API_KEY", "synthetic")
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "runId": "remote-id",
                "status": "COMPLETED",
                "providerResponse": {"httpStatus": 429},
            },
        )

    request = OperationRequest(
        "monid.run",
        {"provider": "apify", "endpoint": "/example", "input": {}},
        allow_paid=True,
    )
    with pytest.raises(CapabilityError, match="provider_failed"):
        CloudProvider().monid(request, tmp_path, client_for(respond))
    assert len(calls) == 1
    assert (tmp_path / "submission.json").exists()


def test_fal_polls_returned_urls_without_submitting_twice(tmp_path, monkeypatch):
    monkeypatch.setenv("FAL_KEY", "synthetic")
    calls = []
    status_url = "https://queue.fal.run/fal-ai/flux/requests/request-id/status"
    response_url = "https://queue.fal.run/fal-ai/flux/requests/request-id"

    def respond(request):
        calls.append(request)
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "request_id": "request-id",
                    "status_url": status_url,
                    "response_url": response_url,
                },
            )
        return httpx.Response(
            200,
            json={"status": "COMPLETED"}
            if str(request.url) == status_url
            else {"images": []},
        )

    request = OperationRequest(
        "fal.run",
        {"endpoint": "fal-ai/flux/schnell", "input": {"prompt": "cat"}},
        allow_paid=True,
    )
    result = CloudProvider().fal(request, tmp_path, client_for(respond))
    assert result == {"images": []}
    assert [call.method for call in calls] == ["POST", "GET", "GET"]
    assert (
        json.loads((tmp_path / "submission.json").read_text())["request_id"]
        == "request-id"
    )


def test_fal_refuses_to_forward_credentials_to_another_host(tmp_path, monkeypatch):
    monkeypatch.setenv("FAL_KEY", "synthetic")
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "request_id": "id",
                "status_url": "https://other.example/status",
                "response_url": "https://other.example/result",
            },
        )

    request = OperationRequest(
        "fal.run", {"endpoint": "fal-ai/flux/schnell", "input": {}}, allow_paid=True
    )
    with pytest.raises(CapabilityError, match="invalid_provider_url"):
        CloudProvider().fal(request, tmp_path, client_for(respond))
    assert len(calls) == 1


@pytest.mark.parametrize("status", [401, 429, 500])
def test_transport_never_retries_submission(status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, json={"error": "synthetic"})

    with pytest.raises(CapabilityError):
        client_for(respond).json("POST", "https://api.monid.ai/v1/run", {})
    assert len(calls) == 1
