import home_assistant_light_control
import pytest

HOME_ASSISTANT_COMMAND_MODULE = home_assistant_light_control


class TestMainEntryPoint:
    def test_exits_with_no_arguments(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["ha-light"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_exits_with_unknown_command(self, monkeypatch, access_token):
        monkeypatch.setattr("sys.argv", ["ha-light", "dance"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_on_command_calls_turn_on(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "on", "bedroom"])
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 1
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/services/light/turn_on"
        )

    def test_off_command_calls_turn_off(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "off", "all"])
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 4

    def test_set_command_with_brightness(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr(
            "sys.argv", ["ha-light", "set", "bedroom", "--brightness", "200"]
        )
        home_assistant_light_control.main()
        assert mock_home_assistant_api_request[0]["payload"]["brightness"] == 200

    def test_set_command_exits_without_attributes(self, monkeypatch, access_token):
        monkeypatch.setattr("sys.argv", ["ha-light", "set", "bedroom"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_status_command_defaults_to_all(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "status"])
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 4

    def test_scene_command_activates_scene(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "scene", "high_warm"])
        home_assistant_light_control.main()
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/services/scene/turn_on"
        )

    def test_on_command_with_brightness_and_temp(
        self,
        monkeypatch,
        access_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr(
            "sys.argv",
            ["ha-light", "on", "all", "--brightness", "180", "--temp", "3500"],
        )
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 4
        for call in mock_home_assistant_api_request:
            assert call["payload"]["brightness"] == 180
            assert call["payload"]["color_temp_kelvin"] == 3500
