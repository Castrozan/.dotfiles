import subprocess
from unittest.mock import MagicMock

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


class TestUnavailableStateRecovery:
    def test_calls_recovery_when_unavailable(
        self, mock_toggle_token, mock_toggle_api_request, monkeypatch
    ):
        calls, ac_state = mock_toggle_api_request
        call_count = {"n": 0}

        def stateful_request(token, endpoint, payload=None):
            calls.append({"token": token, "endpoint": endpoint, "payload": payload})
            if endpoint.startswith("/api/states/"):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return {"state": "unavailable"}
                return {"state": "off"}
            return None

        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle,
            "make_home_assistant_api_request",
            stateful_request,
        )

        fake_result = MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle.subprocess,
            "run",
            lambda *args, **kwargs: fake_result,
        )
        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle.time,
            "sleep",
            lambda s: None,
        )

        home_assistant_air_conditioner_toggle.main()

        turn_on_call = [
            c for c in calls if c["endpoint"] == "/api/services/climate/turn_on"
        ]
        assert len(turn_on_call) == 1

    def test_exits_when_recovery_fails(
        self, mock_toggle_token, mock_toggle_api_request, monkeypatch
    ):
        _, ac_state = mock_toggle_api_request
        ac_state["state"] = "unavailable"

        fake_result = MagicMock()
        fake_result.returncode = 1
        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle.subprocess,
            "run",
            lambda *args, **kwargs: fake_result,
        )

        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_toggle.main()

    def test_exits_when_still_unavailable_after_recovery(
        self, mock_toggle_token, mock_toggle_api_request, monkeypatch
    ):
        _, ac_state = mock_toggle_api_request
        ac_state["state"] = "unavailable"

        fake_result = MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle.subprocess,
            "run",
            lambda *args, **kwargs: fake_result,
        )
        monkeypatch.setattr(
            home_assistant_air_conditioner_toggle.time,
            "sleep",
            lambda s: None,
        )

        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_toggle.main()
