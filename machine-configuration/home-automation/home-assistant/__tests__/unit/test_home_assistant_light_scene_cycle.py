import pytest

import home_assistant_light_scene_cycle


@pytest.fixture
def mock_scene_token(tmp_path, monkeypatch):
    token_file = tmp_path / "home-assistant-token"
    token_file.write_text("fake-ha-token-for-testing")
    monkeypatch.setattr(
        home_assistant_light_scene_cycle,
        "HOME_ASSISTANT_TOKEN_PATH",
        token_file,
    )
    return "fake-ha-token-for-testing"


@pytest.fixture
def mock_scene_api_request(monkeypatch):
    recorded_calls = []

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        return None

    monkeypatch.setattr(
        home_assistant_light_scene_cycle,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls


@pytest.fixture
def mock_scene_state_file(tmp_path, monkeypatch):
    state_file = tmp_path / "ha-light-scene-cycle-index"
    monkeypatch.setattr(
        home_assistant_light_scene_cycle,
        "SCENE_CYCLE_STATE_FILE",
        state_file,
    )
    return state_file


class TestReadCurrentSceneCycleIndex:
    def test_returns_negative_one_when_no_file(self, mock_scene_state_file):
        assert home_assistant_light_scene_cycle.read_current_scene_cycle_index() == -1

    def test_reads_stored_index(self, mock_scene_state_file):
        mock_scene_state_file.write_text("2")
        assert home_assistant_light_scene_cycle.read_current_scene_cycle_index() == 2

    def test_returns_negative_one_on_invalid_content(self, mock_scene_state_file):
        mock_scene_state_file.write_text("garbage")
        assert home_assistant_light_scene_cycle.read_current_scene_cycle_index() == -1


class TestWriteSceneCycleIndex:
    def test_writes_index_to_file(self, mock_scene_state_file):
        home_assistant_light_scene_cycle.write_scene_cycle_index(3)
        assert mock_scene_state_file.read_text() == "3"


class TestCycleStepDefinitions:
    def test_every_step_stays_inside_the_ranges_the_bulbs_report(self):
        for step in home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS:
            assert (
                0
                < step["brightness"]
                <= (home_assistant_light_scene_cycle.MAXIMUM_BRIGHTNESS)
            )
            assert (
                home_assistant_light_scene_cycle.MINIMUM_COLOR_TEMPERATURE_KELVIN
                <= step["color_temp_kelvin"]
                <= home_assistant_light_scene_cycle.MAXIMUM_COLOR_TEMPERATURE_KELVIN
            )

    def test_step_names_are_unique(self):
        names = [
            step["name"]
            for step in home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS
        ]
        assert len(names) == len(set(names))


class TestMainCyclesBehavior:
    def test_first_call_drives_every_light_with_the_first_step(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        home_assistant_light_scene_cycle.main()

        first_step = home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS[0]
        assert [call["endpoint"] for call in mock_scene_api_request] == [
            "/api/services/light/turn_on"
        ] * len(home_assistant_light_scene_cycle.CYCLED_LIGHT_ENTITY_IDS)
        assert [call["payload"]["entity_id"] for call in mock_scene_api_request] == (
            home_assistant_light_scene_cycle.CYCLED_LIGHT_ENTITY_IDS
        )
        for call in mock_scene_api_request:
            assert call["payload"]["brightness"] == first_step["brightness"]
            assert (
                call["payload"]["color_temp_kelvin"] == first_step["color_temp_kelvin"]
            )
        assert mock_scene_state_file.read_text() == "0"
        assert first_step["name"] in capsys.readouterr().out

    def test_never_calls_the_dead_scene_service(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
    ):
        home_assistant_light_scene_cycle.main()

        assert not any(
            "scene" in call["endpoint"] for call in mock_scene_api_request
        ), "scene.* entities carry no targets, so scene/turn_on silently does nothing"

    def test_cycles_to_next_step(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        mock_scene_state_file.write_text("0")
        home_assistant_light_scene_cycle.main()

        second_step = home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS[1]
        assert (
            mock_scene_api_request[0]["payload"]["brightness"]
            == (second_step["brightness"])
        )
        assert mock_scene_state_file.read_text() == "1"
        assert second_step["name"] in capsys.readouterr().out

    def test_wraps_around_to_first_step(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        last_index = len(home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS) - 1
        mock_scene_state_file.write_text(str(last_index))
        home_assistant_light_scene_cycle.main()

        first_step = home_assistant_light_scene_cycle.LIGHT_SCENE_CYCLE_STEPS[0]
        assert (
            mock_scene_api_request[0]["payload"]["brightness"]
            == (first_step["brightness"])
        )
        assert mock_scene_state_file.read_text() == "0"
        assert first_step["name"] in capsys.readouterr().out
