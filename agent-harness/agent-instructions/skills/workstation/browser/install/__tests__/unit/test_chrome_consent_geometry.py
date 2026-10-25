import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_helper as helper
import chrome_consent_geometry as geometry


def test_scrolling_layout_settles_before_capture_and_restores(tmp_path, monkeypatch):
    target = {
        "address": "chrome",
        "pid": 123,
        "process_start": "456",
        "at": [2, 1082],
        "size": [1916, 1076],
    }
    state = {"target": target, "focus": "original", "cursor": (1496, 416)}
    captures = []

    def focus(configuration, address):
        state["focus"] = address
        state["target"] = {**target, "at": [2, 2]}

    def capture(configuration, observed, directory):
        captures.append(observed["at"])
        assert observed["at"] == [2, 2], (
            "Captured stale off-screen geometry after focusing Chrome"
        )

    monkeypatch.setattr(helper, "consume_token", lambda *args: target)
    monkeypatch.setattr(helper, "current_target", lambda *args: state["target"])
    monkeypatch.setattr(helper, "focused_window", lambda *args: state["focus"])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(helper, "focus_window", focus)
    monkeypatch.setattr(
        helper, "move_cursor", lambda configuration, value: state.update(cursor=value)
    )
    monkeypatch.setattr(helper, "capture_dialog", capture)
    monkeypatch.setattr(helper, "dismiss_failed_attempt", lambda *args: None)
    monkeypatch.setattr(geometry, "focused_window", lambda *args: state["focus"])
    monkeypatch.setattr(geometry, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(geometry, "current_target", lambda *args: state["target"])
    monkeypatch.setattr(
        geometry, "monitor_rectangles", lambda *args: [(0, 0, 1920, 1080)]
    )

    def expired(*args):
        raise RuntimeError("deadline")

    monkeypatch.setattr(helper, "await_consent", expired)
    with pytest.raises(RuntimeError, match="deadline"):
        helper.watch({}, tmp_path, "token", 1)
    assert captures == [[2, 2]]
    assert state["focus"] == "original"
    assert state["cursor"] == (1496, 416)


@pytest.mark.parametrize("user_moved", [False, True])
def test_clamped_parking_failure_restores_only_controlled_view(monkeypatch, user_moved):
    target = {
        "address": "chrome",
        "pid": 123,
        "process_start": "456",
        "at": [2, 1082],
        "size": [1916, 1076],
    }
    state = {"focus": "original", "cursor": (1496, 416)}
    moves = []
    monkeypatch.setattr(helper, "focused_window", lambda *args: state["focus"])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(
        helper, "focus_window", lambda configuration, value: state.update(focus=value)
    )
    monkeypatch.setattr(
        helper, "settle_focused_target", lambda *args: (target, (0, 0, 1920, 1080))
    )
    monkeypatch.setattr(helper, "verify_unchanged_attempt", lambda *args: None)

    def move(configuration, position):
        state["cursor"] = (min(position[0], 1919), min(position[1], 1079))
        moves.append(position)

    monkeypatch.setattr(helper, "move_cursor", move)
    with pytest.raises(RuntimeError, match="capture failed"):
        with helper.focused_view({}, target, 1):
            if user_moved:
                state["cursor"] = (600, 500)
            raise RuntimeError("capture failed")
    assert moves[0] == (42, 1079)
    assert state == (
        {"focus": "chrome", "cursor": (600, 500)}
        if user_moved
        else {"focus": "original", "cursor": (1496, 416)}
    )


@pytest.mark.parametrize("changed", ["process", "focus", "cursor", "offscreen"])
def test_unsettled_or_changed_target_never_reaches_capture(monkeypatch, changed):
    target = {
        "address": "chrome",
        "pid": 123,
        "process_start": "456",
        "at": [2, 2],
        "size": [1916, 1076],
    }
    clock = {"value": 0}
    observed = {**target}
    if changed == "process":
        observed["process_start"] = "new"
    if changed == "offscreen":
        observed["at"] = [2, 1082]
    monkeypatch.setattr(geometry.time, "monotonic", lambda: clock["value"])
    monkeypatch.setattr(
        geometry.time, "sleep", lambda delay: clock.update(value=clock["value"] + delay)
    )
    monkeypatch.setattr(
        geometry,
        "focused_window",
        lambda *args: "user" if changed == "focus" else "chrome",
    )
    monkeypatch.setattr(
        geometry,
        "cursor_position",
        lambda *args: (20, 20) if changed == "cursor" else (10, 20),
    )
    monkeypatch.setattr(geometry, "current_target", lambda *args: observed)
    monkeypatch.setattr(
        geometry, "monitor_rectangles", lambda *args: [(0, 0, 1920, 1080)]
    )
    with pytest.raises(RuntimeError, match="changed|deadline"):
        geometry.settle_focused_target({}, target, (10, 20), 20)
    assert clock["value"] <= 2


@pytest.mark.parametrize(
    "scale,transform,disabled,expected",
    [
        (1, 0, False, [(0, 0, 1920, 1080)]),
        (2, 0, False, []),
        (1, 1, False, []),
        (1, 0, True, []),
    ],
)
def test_only_supported_monitor_coordinates_are_used(
    monkeypatch, scale, transform, disabled, expected
):
    import json

    monitor = {
        "x": 0,
        "y": 0,
        "width": 1920,
        "height": 1080,
        "scale": scale,
        "transform": transform,
        "disabled": disabled,
    }
    monkeypatch.setattr(geometry, "run_tool", lambda *args: json.dumps([monitor]))
    assert geometry.monitor_rectangles({}) == expected


def test_input_during_focus_restoration_is_not_overwritten(monkeypatch):
    state = {"focus": "chrome", "cursor": (42, 22)}
    monkeypatch.setattr(helper, "focused_window", lambda *args: state["focus"])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(
        helper,
        "focus_window",
        lambda *args: state.update(focus="original", cursor=(600, 500)),
    )
    monkeypatch.setattr(
        helper, "move_cursor", lambda *args: pytest.fail("overwrote later cursor input")
    )
    helper.restore_view({}, {"address": "chrome"}, (42, 22), (1496, 416), "original")
    assert state["cursor"] == (600, 500)
