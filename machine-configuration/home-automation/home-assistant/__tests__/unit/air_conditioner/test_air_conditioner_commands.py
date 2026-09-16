import home_assistant_air_conditioner_control

HOME_ASSISTANT_COMMAND_MODULE = home_assistant_air_conditioner_control


class TestTurnOnAirConditioner:
    def test_sends_turn_on_request(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.turn_on_air_conditioner(access_token)
        assert len(mock_ac_api_request) == 1
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_on"
        assert (
            mock_ac_api_request[0]["payload"]["entity_id"]
            == home_assistant_air_conditioner_control.AIR_CONDITIONER_ENTITY_ID
        )


class TestTurnOffAirConditioner:
    def test_sends_turn_off_request(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.turn_off_air_conditioner(access_token)
        assert len(mock_ac_api_request) == 1
        assert mock_ac_api_request[0]["endpoint"] == "/api/services/climate/turn_off"


class TestGetAirConditionerStatus:
    def test_prints_status_info(self, access_token, mock_ac_api_request, capsys):
        home_assistant_air_conditioner_control.get_air_conditioner_status(access_token)
        output = capsys.readouterr().out
        assert "state: cool" in output
        assert "indoor_temperature: 23.5" in output
        assert "target_temperature: 24.0" in output
        assert "fan_mode: auto" in output


class TestSetAirConditionerHvacMode:
    def test_sends_set_hvac_mode_request(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_hvac_mode(
            access_token, "cool"
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"] == "/api/services/climate/set_hvac_mode"
        )
        assert mock_ac_api_request[0]["payload"]["hvac_mode"] == "cool"


class TestSetAirConditionerTemperature:
    def test_sends_set_temperature_request(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_temperature(
            access_token, 22.0
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"]
            == "/api/services/climate/set_temperature"
        )
        assert mock_ac_api_request[0]["payload"]["temperature"] == 22.0


class TestSetAirConditionerFanMode:
    def test_sends_set_fan_mode_request(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.set_air_conditioner_fan_mode(
            access_token, "high"
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"] == "/api/services/climate/set_fan_mode"
        )
        assert mock_ac_api_request[0]["payload"]["fan_mode"] == "high"


class TestApplyAirConditionerAttributes:
    def test_applies_all_attributes(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.apply_air_conditioner_attributes(
            access_token,
            {
                "hvac_mode": "cool",
                "temperature": 22.0,
                "fan_mode": "high",
                "swing_mode": "vertical",
                "preset_mode": "eco",
            },
        )
        assert len(mock_ac_api_request) == 5

    def test_applies_only_specified_attributes(self, access_token, mock_ac_api_request):
        home_assistant_air_conditioner_control.apply_air_conditioner_attributes(
            access_token, {"temperature": 20.0}
        )
        assert len(mock_ac_api_request) == 1
        assert (
            mock_ac_api_request[0]["endpoint"]
            == "/api/services/climate/set_temperature"
        )
