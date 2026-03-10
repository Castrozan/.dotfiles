import pytest

import home_assistant_air_conditioner_toggle


@pytest.fixture
def mock_toggle_token(tmp_path, monkeypatch):
    token_file = tmp_path / "home-assistant-token"
    token_file.write_text("fake-ha-token-for-testing")
    monkeypatch.setattr(
        home_assistant_air_conditioner_toggle,
        "HOME_ASSISTANT_TOKEN_PATH",
        token_file,
    )
    return "fake-ha-token-for-testing"


@pytest.fixture
def mock_toggle_api_request(monkeypatch):
    recorded_calls = []
    ac_state = {"state": "off"}

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        if endpoint.startswith("/api/states/"):
            return ac_state
        return None

    monkeypatch.setattr(
        home_assistant_air_conditioner_toggle,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls, ac_state


class TestGetCurrentAirConditionerState:
    def test_returns_off_when_off(self, mock_toggle_token, mock_toggle_api_request):
        _, ac_state = mock_toggle_api_request
        ac_state["state"] = "off"
        result = (
            home_assistant_air_conditioner_toggle.get_current_air_conditioner_state(
                mock_toggle_token
            )
        )
        assert result == "off"

    def test_returns_cool_when_cooling(
        self, mock_toggle_token, mock_toggle_api_request
    ):
        _, ac_state = mock_toggle_api_request
        ac_state["state"] = "cool"
        result = (
            home_assistant_air_conditioner_toggle.get_current_air_conditioner_state(
                mock_toggle_token
            )
        )
        assert result == "cool"


class TestMainToggleBehavior:
    def test_turns_on_when_off(
        self, mock_toggle_token, mock_toggle_api_request, capsys
    ):
        calls, ac_state = mock_toggle_api_request
        ac_state["state"] = "off"
        home_assistant_air_conditioner_toggle.main()
        turn_on_call = calls[1]
        assert turn_on_call["endpoint"] == "/api/services/climate/turn_on"
        assert "on" in capsys.readouterr().out

    def test_turns_off_when_cooling(
        self, mock_toggle_token, mock_toggle_api_request, capsys
    ):
        calls, ac_state = mock_toggle_api_request
        ac_state["state"] = "cool"
        home_assistant_air_conditioner_toggle.main()
        turn_off_call = calls[1]
        assert turn_off_call["endpoint"] == "/api/services/climate/turn_off"
        assert "off" in capsys.readouterr().out

    def test_turns_off_when_heating(
        self, mock_toggle_token, mock_toggle_api_request, capsys
    ):
        calls, ac_state = mock_toggle_api_request
        ac_state["state"] = "heat"
        home_assistant_air_conditioner_toggle.main()
        turn_off_call = calls[1]
        assert turn_off_call["endpoint"] == "/api/services/climate/turn_off"

    def test_turns_off_when_auto(
        self, mock_toggle_token, mock_toggle_api_request, capsys
    ):
        calls, ac_state = mock_toggle_api_request
        ac_state["state"] = "auto"
        home_assistant_air_conditioner_toggle.main()
        turn_off_call = calls[1]
        assert turn_off_call["endpoint"] == "/api/services/climate/turn_off"
