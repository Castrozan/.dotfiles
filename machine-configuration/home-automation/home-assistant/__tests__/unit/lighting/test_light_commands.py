import home_assistant_light_control

HOME_ASSISTANT_COMMAND_MODULE = home_assistant_light_control


class TestTurnOnLights:
    def test_sends_turn_on_request_for_each_entity(
        self, access_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_on_lights(
            access_token,
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
        self, access_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_on_lights(
            access_token,
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
        self, access_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.turn_off_lights(
            access_token,
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
        self, access_token, mock_home_assistant_api_request, capsys
    ):
        home_assistant_light_control.get_light_states(
            access_token,
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
        self, access_token, mock_home_assistant_api_request
    ):
        home_assistant_light_control.activate_scene(
            access_token,
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
