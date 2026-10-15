import pytest

from ambient_canvas_mpv_visibility import player_is_visible


@pytest.fixture
def compositor_state():
    return {
        "clients": [
            {
                "pid": 14534,
                "workspace": {"id": 11},
                "at": [2, 2],
                "size": [1916, 1076],
                "mapped": True,
                "hidden": False,
                "fullscreen": 0,
            }
        ],
        "monitors": [
            {
                "id": 0,
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "scale": 1,
                "activeWorkspace": {"id": 11},
            }
        ],
    }


@pytest.mark.parametrize(
    ("position", "visible"),
    [([2, 2], True), ([2, -1078], False), ([1920, 2], False), ([1919, 2], True)],
)
def test_actual_viewport_intersection(compositor_state, position, visible):
    compositor_state["clients"][0]["at"] = position
    assert (
        player_is_visible(
            **compositor_state, player_process_id=14534, target_workspace_id=11
        )
        is visible
    )


@pytest.mark.parametrize("field,value", [("hidden", True), ("mapped", False)])
def test_hidden_or_unmapped_player_is_not_visible(compositor_state, field, value):
    compositor_state["clients"][0][field] = value
    assert not player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )


def test_canvas_visible_on_another_active_monitor_keeps_playing(compositor_state):
    compositor_state["clients"][0]["at"] = [1922, 2]
    compositor_state["monitors"][0]["activeWorkspace"] = {"id": 5}
    compositor_state["monitors"].append(
        {
            **compositor_state["monitors"][0],
            "id": 1,
            "x": 1920,
            "activeWorkspace": {"id": 11},
        }
    )
    assert player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )


def test_inactive_workspace_or_another_player_is_not_visible(compositor_state):
    compositor_state["monitors"][0]["activeWorkspace"] = {"id": 5}
    assert not player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )
    compositor_state["monitors"][0]["activeWorkspace"] = {"id": 11}
    assert not player_is_visible(
        **compositor_state, player_process_id=99999, target_workspace_id=11
    )


@pytest.mark.parametrize("transform", [0, 1])
def test_scaled_rotated_monitor_uses_logical_coordinates(compositor_state, transform):
    compositor_state["monitors"][0].update(
        width=3840, height=2160, scale=2, transform=transform
    )
    compositor_state["clients"][0]["at"] = [1500, 2]
    assert player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    ) is (transform == 0)


def test_fullscreen_game_covering_canvas_pauses(compositor_state):
    compositor_state["clients"].append(
        {
            **compositor_state["clients"][0],
            "pid": 90000,
            "fullscreen": 2,
            "at": [0, 0],
            "size": [1920, 1080],
        }
    )
    assert not player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )
    compositor_state["clients"][1]["hidden"] = True
    assert player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )


@pytest.mark.parametrize("field,value", [("disabled", True), ("dpmsStatus", False)])
def test_inactive_display_does_not_keep_canvas_playing(compositor_state, field, value):
    compositor_state["monitors"][0][field] = value
    assert not player_is_visible(
        **compositor_state, player_process_id=14534, target_workspace_id=11
    )
