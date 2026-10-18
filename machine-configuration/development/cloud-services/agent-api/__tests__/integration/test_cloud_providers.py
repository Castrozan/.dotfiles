import json
from pathlib import Path

import httpx
import pytest

from agent_api.catalog import validate_request
from agent_api.contract import CapabilityError, OperationRequest
from agent_api.providers import firecrawl
from agent_api.providers.network import NetworkClient


def client_for(handler):
    return NetworkClient(10, httpx.Client(transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("credential_source", ["environment", "file"])
@pytest.mark.parametrize(
    ("capability", "input_data"),
    [
        ("web.search", {"query": "documentation", "limit": 2}),
        ("web.scrape", {"url": "https://example.com"}),
    ],
)
def test_firecrawl_never_uses_account_credentials(
    tmp_path, monkeypatch, credential_source, capability, input_data
):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    if credential_source == "environment":
        monkeypatch.setenv("FIRECRAWL_API_KEY", "synthetic")
    else:
        secrets_directory = tmp_path / ".secrets"
        secrets_directory.mkdir()
        (secrets_directory / "firecrawl-api-key").write_text("synthetic")
    calls = []

    def respond(request):
        calls.append(request)
        assert "authorization" not in request.headers
        assert request.url.path == "/v2/" + capability.removeprefix("web.")
        data = json.loads(request.content)
        assert all(data[name] == value for name, value in input_data.items())
        if capability == "web.scrape":
            assert data["formats"] == ["markdown"]
            assert data["onlyMainContent"] is True
        return httpx.Response(200, json={"success": True, "data": []})

    monkeypatch.setattr(firecrawl, "NetworkClient", lambda timeout: client_for(respond))
    for allow_paid in (False, True):
        request = OperationRequest(capability, input_data, allow_paid=allow_paid)
        assert validate_request(request)["payment"] == "none"
        assert firecrawl.FirecrawlProvider().execute(request, tmp_path, "id") == {
            "success": True,
            "data": [],
        }
    assert len(calls) == 2


def test_firecrawl_rejects_unsuccessful_provider_responses(tmp_path, monkeypatch):
    monkeypatch.setattr(
        firecrawl,
        "NetworkClient",
        lambda timeout: client_for(
            lambda request: httpx.Response(200, json={"success": False})
        ),
    )
    with pytest.raises(CapabilityError, match="provider_failed"):
        firecrawl.FirecrawlProvider().execute(
            OperationRequest("web.search", {"query": "documentation"}), tmp_path, "id"
        )


@pytest.mark.parametrize("status", [401, 429, 500])
def test_transport_never_retries_submission(status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, json={"error": "synthetic"})

    with client_for(respond) as client:
        with pytest.raises(CapabilityError):
            client.json("POST", "https://api.firecrawl.dev/v2/search", {})
    assert len(calls) == 1
