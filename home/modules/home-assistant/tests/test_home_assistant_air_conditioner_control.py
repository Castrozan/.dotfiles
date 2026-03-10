import pytest

import home_assistant_air_conditioner_control


@pytest.fixture
def mock_ac_token(tmp_path, monkeypatch):
    token_file = tmp_path / "home-assistant-token"
    token_file.write_text("fake-ha-token-for-testing")
    monkeypatch.setattr(
        home_assistant_air_conditioner_control,
        "HOME_ASSISTANT_TOKEN_PATH",
        token_file,
    )
    return "fake-ha-token-for-testing"


@pytest.fixture
def mock_ac_api_request(monkeypatch):
    recorded_calls = []

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        if endpoint.startswith("/api/states/"):
            return {
                "state": "cool",
                "attributes": {
                    "indoor_temperature": 23.5,
                    "temperature": 24.0,
                    "fan_mode": "auto",
                    "swing_mode": "off",
                    "preset_mode": "none",
                    "realtime_power": 850.0,
                    "total_energy_consumption": 120.5,
                },
            }
        return None

    monkeypatch.setattr(
        home_assistant_air_conditioner_control,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls


class TestValidateTemperature:
    def test_accepts_minimum(self):
        assert home_assistant_air_conditioner_control.validate_temperature("16") == 16.0

    def test_accepts_maximum(self):
        assert home_assistant_air_conditioner_control.validate_temperature("30") == 30.0

    def test_accepts_half_degree(self):
        assert (
            home_assistant_air_conditioner_control.validate_temperature("22.5") == 22.5
        )

    def test_rejects_below_minimum(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_temperature("15")

    def test_rejects_above_maximum(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_temperature("31")


class TestValidateHvacMode:
    def test_accepts_cool(self):
        assert (
            home_assistant_air_conditioner_control.validate_hvac_mode("cool") == "cool"
        )

    def test_accepts_heat(self):
        assert (
            home_assistant_air_conditioner_control.validate_hvac_mode("heat") == "heat"
        )

    def test_accepts_auto(self):
        assert (
            home_assistant_air_conditioner_control.validate_hvac_mode("auto") == "auto"
        )

    def test_accepts_fan_only(self):
        assert (
            home_assistant_air_conditioner_control.validate_hvac_mode("fan_only")
            == "fan_only"
        )

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_hvac_mode("turbo")


class TestValidateFanMode:
    def test_accepts_silent(self):
        assert (
            home_assistant_air_conditioner_control.validate_fan_mode("silent")
            == "silent"
        )

    def test_accepts_auto(self):
        assert (
            home_assistant_air_conditioner_control.validate_fan_mode("auto") == "auto"
        )

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_fan_mode("turbo")


class TestValidateSwingMode:
    def test_accepts_vertical(self):
        assert (
            home_assistant_air_conditioner_control.validate_swing_mode("vertical")
            == "vertical"
        )

    def test_accepts_both(self):
        assert (
            home_assistant_air_conditioner_control.validate_swing_mode("both") == "both"
        )

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_swing_mode("diagonal")


class TestValidatePresetMode:
    def test_accepts_eco(self):
        assert (
            home_assistant_air_conditioner_control.validate_preset_mode("eco") == "eco"
        )

    def test_accepts_boost(self):
        assert (
            home_assistant_air_conditioner_control.validate_preset_mode("boost")
            == "boost"
        )

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.validate_preset_mode("max")


class TestParseSetCommandArguments:
    def test_parses_temp_flag(self):
        result = home_assistant_air_conditioner_control.parse_set_command_arguments(
            ["--temp", "22"]
        )
        assert result == {"temperature": 22.0}

    def test_parses_fan_flag(self):
        result = home_assistant_air_conditioner_control.parse_set_command_arguments(
            ["--fan", "high"]
        )
        assert result == {"fan_mode": "high"}

    def test_parses_multiple_flags(self):
        result = home_assistant_air_conditioner_control.parse_set_command_arguments(
            ["--temp", "20", "--fan", "low", "--mode", "cool"]
        )
        assert result == {
            "temperature": 20.0,
            "fan_mode": "low",
            "hvac_mode": "cool",
        }

    def test_parses_all_flags(self):
        result = home_assistant_air_conditioner_control.parse_set_command_arguments(
            [
                "--temp",
                "25",
                "--fan",
                "auto",
                "--swing",
                "both",
                "--mode",
                "heat",
                "--preset",
                "eco",
            ]
        )
        assert result == {
            "temperature": 25.0,
            "fan_mode": "auto",
            "swing_mode": "both",
            "hvac_mode": "heat",
            "preset_mode": "eco",
        }

    def test_returns_empty_dict_for_no_arguments(self):
        result = home_assistant_air_conditioner_control.parse_set_command_arguments([])
        assert result == {}

    def test_exits_on_unknown_flag(self):
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.parse_set_command_arguments(
                ["--color", "red"]
            )


class TestTurnOnAirConditioner:
    def test_sends_turn_on_request(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.turn_on_air_conditioner(mock_ac_token)
        assert len(mock_ac_api_request) == 1
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_on"
        assert (
            mock_ac_api_request[0]["payload"]["entity_id"]
            == home_assistant_air_conditioner_control.AIR_CONDITIONER_ENTITY_ID
        )


class TestTurnOffAirConditioner:
    def test_sends_turn_off_request(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.turn_off_air_conditioner(mock_ac_token)
        assert len(mock_ac_api_request) == 1
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_off"


class TestGetAirConditionerStatus:
    def test_prints_status_info(self, mock_ac_token, mock_ac_api_request, capsys):
        home_assistant_air_conditioner_control.get_air_conditioner_status(mock_ac_token)
        output = capsys.readouterr().out
        assert "state: cool" in output
        assert "indoor_temperature: 23.5" in output
        assert "target_temperature: 24.0" in output
        assert "fan_mode: auto" in output


class TestSetAirConditionerHvacMode:
    def test_sends_set_hvac_mode_request(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_hvac_mode(
            mock_ac_token, "cool"
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"] == "/api/services/climate/set_hvac_mode"
        )
        assert mock_ac_api_request[0]["payload"]["hvac_mode"] == "cool"


class TestSetAirConditionerTemperature:
    def test_sends_set_temperature_request(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_temperature(
            mock_ac_token, 22.0
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"]
            == "/api/services/climate/set_temperature"
        )
        assert mock_ac_api_request[0]["payload"]["temperature"] == 22.0


class TestSetAirConditionerFanMode:
    def test_sends_set_fan_mode_request(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_fan_mode(
            mock_ac_token, "high"
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"] == "/api/services/climate/set_fan_mode"
        )
        assert mock_ac_api_request[0]["payload"]["fan_mode"] == "high"


class TestApplyAirConditionerAttributes:
    def test_applies_all_attributes(self, mock_ac_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.apply_air_conditioner_attributes(
            mock_ac_token,
            {
                "hvac_mode": "cool",
                "temperature": 22.0,
                "fan_mode": "high",
                "swing_mode": "vertical",
                "preset_mode": "eco",
            },
        )
        assert len(mock_ac_api_request) == 5

    def test_applies_only_specified_attributes(
        self, mock_ac_token, mock_ac_api_request
    ):
        home_assistant_air_conditioner_control.apply_air_conditioner_attributes(
            mock_ac_token, {"temperature": 20.0}
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"]
            == "/api/services/climate/set_temperature"
        )


class TestMainEntryPoint:
    def test_exits_with_no_arguments(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["ha-ac"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()

    def test_exits_with_unknown_command(self, monkeypatch, mock_ac_token):
        monkeypatch.setattr("sys.argv", ["ha-ac", "dance"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()

    def test_on_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "on"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_on"

    def test_off_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "off"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_off"

    def test_status_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "status"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["endpoint"].startswith("/api/states/")

    def test_mode_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "mode", "heat"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["hvac_mode"] == "heat"

    def test_temp_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "temp", "22"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["temperature"] == 22.0

    def test_fan_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "fan", "high"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["fan_mode"] == "high"

    def test_swing_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "swing", "both"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["swing_mode"] == "both"

    def test_preset_command(self, monkeypatch, mock_ac_token, mock_ac_api_request):
        monkeypatch.setattr("sys.argv", ["ha-ac", "preset", "eco"])
        home_assistant_air_conditioner_control.main()
        assert mock_ac_api_request[0]["payload"]["preset_mode"] == "eco"

    def test_set_command_with_multiple_attributes(
        self, monkeypatch, mock_ac_token, mock_ac_api_request
    ):
        monkeypatch.setattr(
            "sys.argv",
            ["ha-ac", "set", "--temp", "20", "--fan", "low", "--mode", "cool"],
        )
        home_assistant_air_conditioner_control.main()
        assert len(mock_ac_api_request) == 3

    def test_set_command_exits_without_attributes(self, monkeypatch, mock_ac_token):
        monkeypatch.setattr("sys.argv", ["ha-ac", "set"])
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_control.main()
