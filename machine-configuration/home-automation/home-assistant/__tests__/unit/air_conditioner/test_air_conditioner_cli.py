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

    @pytest.mark.parametrize(
        ("arguments", "payload_key", "expected_value"),
        [
            pytest.param(["mode", "heat"], "hvac_mode", "heat", id="mode_command"),
            pytest.param(["temp", "22"], "temperature", 22.0, id="temp_command"),
            pytest.param(["fan", "high"], "fan_mode", "high", id="fan_command"),
            pytest.param(["swing", "both"], "swing_mode", "both", id="swing_command"),
            pytest.param(["preset", "eco"], "preset_mode", "eco", id="preset_command"),
        ],
    )
    def test_attribute_command_sends_its_value_in_the_payload(
        self,
        monkeypatch,
        access_token,
        mock_ac_api_request,
        arguments,
        payload_key,
        expected_value,
    ):
        monkeypatch.setattr("sys.argv", ["ha-ac", *arguments])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"][payload_key] == expected_value

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
