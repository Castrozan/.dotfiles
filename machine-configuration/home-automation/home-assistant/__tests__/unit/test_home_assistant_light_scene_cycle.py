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


class TestMainCyclesBehavior:
    def test_first_call_activates_first_scene(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        home_assistant_light_scene_cycle.main()
        assert mock_scene_api_request[0]["payload"] == {"entity_id": "scene.low_warm"}
        assert mock_scene_state_file.read_text() == "0"
        assert "low_warm" in capsys.readouterr().out

    def test_cycles_to_next_scene(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        mock_scene_state_file.write_text("0")
        home_assistant_light_scene_cycle.main()
        assert mock_scene_api_request[0]["payload"] == {"entity_id": "scene.half_half"}
        assert mock_scene_state_file.read_text() == "1"

    def test_cycles_through_all_scenes(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
    ):
        mock_scene_state_file.write_text("1")
        home_assistant_light_scene_cycle.main()
        assert mock_scene_api_request[0]["payload"] == {"entity_id": "scene.70_70"}

    def test_wraps_around_to_first_scene(
        self,
        mock_scene_token,
        mock_scene_api_request,
        mock_scene_state_file,
        capsys,
    ):
        mock_scene_state_file.write_text("3")
        home_assistant_light_scene_cycle.main()
        assert mock_scene_api_request[0]["payload"] == {"entity_id": "scene.low_warm"}
        assert mock_scene_state_file.read_text() == "0"
