import home_assistant_air_conditioner_control
import pytest

HOME_ASSISTANT_COMMAND_MODULE = home_assistant_air_conditioner_control


class TestMainEntryPoint:
    def test_exits_with_no_arguments(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["ha-ac"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()

    def test_exits_with_unknown_command(self, monkeypatch, access_token):
        monkeypatch.setattr("sys.argv", ["ha-ac", "dance"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()

    def test_on_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "on"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_on"

    def test_off_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "off"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_off"

    def test_status_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "status"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"].startswith("/api/states/")

    def test_mode_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "mode", "heat"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["hvac_mode"] == "heat"

    def test_temp_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "temp", "22"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["temperature"] == 22.0

    def test_fan_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "fan", "high"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["fan_mode"] == "high"

    def test_swing_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "swing", "both"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["swing_mode"] == "both"

    def test_preset_command(self, monkeypatch, access_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "preset", "eco"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["preset_mode"] == "eco"

    def test_set_command_with_multiple_attributes(
        self, monkeypatch, access_token, mock_ac_api_request
    ):
        monkeypatch.setattr(
            "sys.argv",
            ["ha-ac", "set", "--temp", "20", "--fan", "low", "--mode", "cool"],
        )
        home_assistant_air_conditioner_control.main()
        assert len(mock_ac_api_request) == 3

    def test_set_command_exits_without_attributes(self, monkeypatch, access_token):
        monkeypatch.setattr("sys.argv", ["ha-ac", "set"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()
