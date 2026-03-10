import pytest

import home_assistant_light_control


class TestReadHomeAssistantToken:
    def test_reads_token_from_file(self, tmp_path, monkeypatch):
        token_file = tmp_path / "token"
        token_file.write_text("my-secret-token\n")
        monkeypatch.setattr(
            home_assistant_light_control,
            "HOME_ASSISTANT_TOKEN_PATH",
            token_file,
        )
        assert (
            home_assistant_light_control.read_home_assistant_token()
            == "my-secret-token"
        )

    def test_exits_when_token_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            home_assistant_light_control,
            "HOME_ASSISTANT_TOKEN_PATH",
            tmp_path / "nonexistent",
        )
        with pytest.raises(SystemExit):
            home_assistant_light_control.read_home_assistant_token()


class TestResolveTargetEntityIds:
    def test_resolves_all_to_every_light(self):
        result = home_assistant_light_control.resolve_target_entity_ids("all")
        assert result == home_assistant_light_control.ALL_LIGHT_ENTITY_IDS

    def test_resolves_single_light_name(self):
        result = home_assistant_light_control.resolve_target_entity_ids("bedroom")
        assert result == ["light.bedroom"]

    def test_resolves_kitchen(self):
        result = home_assistant_light_control.resolve_target_entity_ids("kitchen")
        assert result == ["light.kitchen"]

    def test_exits_on_unknown_light_name(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.resolve_target_entity_ids("garage")


class TestParseBrightnessArgument:
    def test_parses_valid_brightness(self):
        assert home_assistant_light_control.parse_brightness_argument("128") == 128

    def test_parses_zero(self):
        assert home_assistant_light_control.parse_brightness_argument("0") == 0

    def test_parses_maximum(self):
        assert home_assistant_light_control.parse_brightness_argument("255") == 255

    def test_exits_on_negative(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_brightness_argument("-1")

    def test_exits_on_too_high(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_brightness_argument("256")


class TestParseColorTemperatureArgument:
    def test_parses_valid_temperature(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("3500")
            == 3500
        )

    def test_parses_minimum(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("2000")
            == 2000
        )

    def test_parses_maximum(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("6500")
            == 6500
        )

    def test_exits_on_too_low(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_color_temperature_argument("1999")

    def test_exits_on_too_high(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_color_temperature_argument("6501")


class TestParseOptionalAttributesFromArguments:
    def test_parses_brightness_flag(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--brightness", "200"]
        )
        assert result == {"brightness": 200}

    def test_parses_temp_flag(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--temp", "4000"]
        )
        assert result == {"color_temp_kelvin": 4000}

    def test_parses_both_flags(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--brightness", "180", "--temp", "3500"]
        )
        assert result == {"brightness": 180, "color_temp_kelvin": 3500}

    def test_returns_empty_dict_for_no_arguments(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            []
        )
        assert result == {}

    def test_exits_on_unknown_flag(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_optional_attributes_from_arguments(
                ["--color", "red"]
            )


class TestTurnOnLights:
    def test_sends_turn_on_request_for_each_entity(
        self, mock_home_assistant_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_on_lights(
            mock_home_assistant_token,
            ["light.bedroom", "light.kitchen"],
            {},
        )
        assert len(mock_home_assistant_api_request) == 2
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/services/light/turn_on"
        )
        assert mock_home_assistant_api_request[0]["payload"] == {
            "entity_id": "light.bedroom"
        }
        assert mock_home_assistant_api_request[1]["payload"] == {
            "entity_id": "light.kitchen"
        }

    def test_includes_extra_attributes_in_payload(
        self, mock_home_assistant_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_on_lights(
            mock_home_assistant_token,
            ["light.bedroom"],
            {"brightness": 200, "color_temp_kelvin": 3500},
        )
        expected_payload = {
            "entity_id": "light.bedroom",
            "brightness": 200,
            "color_temp_kelvin": 3500,
        }
        assert mock_home_assistant_api_request[0]["payload"] == expected_payload


class TestTurnOffLights:
    def test_sends_turn_off_request_for_each_entity(
        self, mock_home_assistant_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_off_lights(
            mock_home_assistant_token,
            ["light.bedroom", "light.kitchen"],
        )
        assert len(mock_home_assistant_api_request) == 2
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/services/light/turn_off"
        )
        assert (
            mock_home_assistant_api_request[1]["endpoint"]
            == "/api/services/light/turn_off"
        )


class TestGetLightStates:
    def test_queries_state_for_each_entity(
        self, mock_home_assistant_token, mock_home_assistant_api_request, capsys
    ):
        home_assistant_light_control.get_light_states(
            mock_home_assistant_token,
            ["light.bedroom"],
        )
        assert len(mock_home_assistant_api_request) == 1
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/states/light.bedroom"
        )
        output = capsys.readouterr().out
        assert "bedroom" in output
        assert "on" in output


class TestActivateScene:
    def test_sends_scene_turn_on_request(
        self, mock_home_assistant_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.activate_scene(
            mock_home_assistant_token,
            "high_warm",
        )
        assert len(mock_home_assistant_api_request) == 1
        assert (
            mock_home_assistant_api_request[0]["endpoint"]
            == "/api/services/scene/turn_on"
        )
        assert mock_home_assistant_api_request[0]["payload"] == {
            "entity_id": "scene.high_warm"
        }


class TestMainEntryPoint:
    def test_exits_with_no_arguments(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["ha-light"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_exits_with_unknown_command(self, monkeypatch, mock_home_assistant_token):
        monkeypatch.setattr("sys.argv", ["ha-light", "dance"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_on_command_calls_turn_on(
        self,
        monkeypatch,
        mock_home_assistant_token,
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
        mock_home_assistant_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "off", "all"])
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 4

    def test_set_command_with_brightness(
        self,
        monkeypatch,
        mock_home_assistant_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr(
            "sys.argv", ["ha-light", "set", "bedroom", "--brightness", "200"]
        )
        home_assistant_light_control.main()
        assert mock_home_assistant_api_request[0]["payload"]["brightness"] == 200

    def test_set_command_exits_without_attributes(
        self, monkeypatch, mock_home_assistant_token
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "set", "bedroom"])
        with pytest.raises(SystemExit):
            home_assistant_light_control.main()

    def test_status_command_defaults_to_all(
        self,
        monkeypatch,
        mock_home_assistant_token,
        mock_home_assistant_api_request,
    ):
        monkeypatch.setattr("sys.argv", ["ha-light", "status"])
        home_assistant_light_control.main()
        assert len(mock_home_assistant_api_request) == 4

    def test_scene_command_activates_scene(
        self,
        monkeypatch,
        mock_home_assistant_token,
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
        mock_home_assistant_token,
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
