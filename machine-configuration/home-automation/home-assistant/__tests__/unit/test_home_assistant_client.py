import json
from types import SimpleNamespace

import pytest

import home_assistant_client


class RecordedHomeAssistantTransport:
    def __init__(self):
        self.sent_requests = []
        self.response_body = ""

    def urlopen(self, request):
        self.sent_requests.append(request)
        return SimpleNamespace(read=lambda: self.response_body.encode())


@pytest.fixture
def recorded_home_assistant_transport(monkeypatch):
    recorded_transport = RecordedHomeAssistantTransport()
    monkeypatch.setattr(
        home_assistant_client.urllib.request,
        "urlopen",
        recorded_transport.urlopen,
    )
    return recorded_transport


class TestReadHomeAssistantToken:
    def test_reads_token_from_file(self, tmp_path, monkeypatch):
        token_file = tmp_path / "token"
        token_file.write_text("my-secret-token\n")
        monkeypatch.setattr(
            home_assistant_client,
            "HOME_ASSISTANT_TOKEN_PATH",
            token_file,
        )
        assert home_assistant_client.read_home_assistant_token() == "my-secret-token"

    def test_exits_when_token_file_missing(self, tmp_path, monkeypatch, capsys):
        missing_token_file = tmp_path / "nonexistent"
        monkeypatch.setattr(
            home_assistant_client,
            "HOME_ASSISTANT_TOKEN_PATH",
            missing_token_file,
        )
        with pytest.raises(SystemExit) as raised_exit:
            home_assistant_client.read_home_assistant_token()
        assert raised_exit.value.code == 1
        assert (
            f"Home Assistant token not found at {missing_token_file}"
            in capsys.readouterr().err
        )


class TestMakeHomeAssistantApiRequest:
    def test_gets_from_the_configured_base_url_with_the_bearer_token(
        self, recorded_home_assistant_transport
    ):
        home_assistant_client.make_home_assistant_api_request(
            "token-value", "/api/states/light.bedroom"
        )
        request = recorded_home_assistant_transport.sent_requests[0]
        assert request.full_url == (
            f"{home_assistant_client.HOME_ASSISTANT_BASE_URL}/api/states/light.bedroom"
        )
        assert request.get_method() == "GET"
        assert request.data is None
        assert request.get_header("Authorization") == "Bearer token-value"
        assert request.get_header("Content-type") == "application/json"

    def test_posts_the_payload_json_encoded(self, recorded_home_assistant_transport):
        home_assistant_client.make_home_assistant_api_request(
            "token-value",
            "/api/services/light/turn_on",
            {"entity_id": "light.bedroom", "brightness": 200},
        )
        request = recorded_home_assistant_transport.sent_requests[0]
        assert request.get_method() == "POST"
        assert json.loads(request.data.decode()) == {
            "entity_id": "light.bedroom",
            "brightness": 200,
        }

    def test_posts_without_a_body_when_the_payload_is_empty(
        self, recorded_home_assistant_transport
    ):
        home_assistant_client.make_home_assistant_api_request(
            "token-value",
            "/api/config/config_entries/entry/test-entry-id/reload",
            {},
        )
        request = recorded_home_assistant_transport.sent_requests[0]
        assert request.get_method() == "POST"
        assert request.data is None

    def test_decodes_a_json_response_body(self, recorded_home_assistant_transport):
        recorded_home_assistant_transport.response_body = '{"state": "on"}'
        result = home_assistant_client.make_home_assistant_api_request(
            "token-value", "/api/states/light.bedroom"
        )
        assert result == {"state": "on"}

    def test_returns_none_for_an_empty_response_body(
        self, recorded_home_assistant_transport
    ):
        result = home_assistant_client.make_home_assistant_api_request(
            "token-value",
            "/api/services/light/turn_on",
            {"entity_id": "light.bedroom"},
        )
        assert result is None
