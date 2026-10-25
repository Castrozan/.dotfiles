from contextlib import contextmanager
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_helper as helper
import chrome_consent_input as native_input
from chrome_consent_dialog import DialogButton


@pytest.mark.parametrize("changed", [False, True])
def test_click_is_single_and_temporary_input_daemon_always_stops(
    tmp_path, monkeypatch, changed
):
    target = {
        "address": "0x123",
        "pid": 123,
        "process_start": "456",
        "at": [0, 0],
        "size": [1920, 1080],
    }
    button = DialogButton((1121, 287), (746, 54, 1186, 313))
    daemon = SimpleNamespace()
    stopped, moved, clicks = [], [], []
    positions = iter([(10, 20), button.position, button.position])
    monkeypatch.setattr(
        native_input.subprocess, "Popen", lambda *args, **kwargs: daemon
    )
    monkeypatch.setattr(
        native_input, "stop_process", lambda process: stopped.append(process)
    )
    monkeypatch.setattr(Path, "exists", lambda self: self.name == "ydotool.sock")
    monkeypatch.setattr(native_input, "focused_window", lambda *args: target["address"])
    monkeypatch.setattr(
        native_input, "capture_dialog", lambda *args: None if changed else button
    )
    monkeypatch.setattr(native_input, "current_target", lambda *args: target)
    monkeypatch.setattr(native_input, "cursor_position", lambda *args: next(positions))
    monkeypatch.setattr(
        native_input,
        "move_cursor",
        lambda configuration, position: moved.append(position),
    )
    monkeypatch.setattr(
        native_input.subprocess,
        "run",
        lambda arguments, **kwargs: clicks.append(arguments),
    )
    if changed:
        with pytest.raises(RuntimeError, match="changed before"):
            native_input.click_once(
                {"ydotoold": "daemon", "ydotool": "input"},
                target,
                button,
                tmp_path,
                (10, 20),
            )
        assert not clicks
        assert not moved
    else:
        native_input.click_once(
            {"ydotoold": "daemon", "ydotool": "input"},
            target,
            button,
            tmp_path,
            (10, 20),
        )
        assert clicks == [["input", "click", "0xC0"]]
        assert moved == [button.position, (10, 20)]
    assert stopped == [daemon]


def test_cursor_is_parked_outside_dialog_before_capture_and_restored(
    tmp_path, monkeypatch
):
    target = {
        "address": "0x123",
        "pid": 123,
        "process_start": "456",
        "at": [2, 2],
        "size": [1916, 1076],
    }
    state = {"cursor": (1121, 287), "focus": "original"}
    moves, captures = [], []

    def move(configuration, value):
        state["cursor"] = value
        moves.append(value)

    monkeypatch.setattr(helper, "consume_token", lambda *args: target)
    monkeypatch.setattr(helper, "dismiss_failed_attempt", lambda *args: None)
    monkeypatch.setattr(helper, "focused_window", lambda *args: state["focus"])
    monkeypatch.setattr(
        helper,
        "focus_window",
        lambda configuration, address: state.update(focus=address),
    )
    monkeypatch.setattr(helper, "current_target", lambda *args: target)
    monkeypatch.setattr(
        helper, "settle_focused_target", lambda *args: (target, (0, 0, 1920, 1080))
    )
    monkeypatch.setattr(helper, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(helper, "move_cursor", move)
    monkeypatch.setattr(
        helper, "capture_dialog", lambda *args: captures.append(state["cursor"])
    )
    with pytest.raises(RuntimeError, match="deadline"):
        helper.watch({}, tmp_path, "token", 0)
    assert captures == [(42, 22)]
    assert moves == [(42, 22), (1121, 287)]
    assert state["focus"] == "original"


def test_user_cursor_movement_during_final_focus_check_aborts_click(
    tmp_path, monkeypatch
):
    target = {
        "address": "0x123",
        "pid": 123,
        "process_start": "456",
        "at": [0, 0],
        "size": [1920, 1080],
    }
    button = DialogButton((1121, 287), (746, 54, 1186, 313))
    state = {"cursor": (10, 20), "focus_checks": 0}

    @contextmanager
    def input_socket(*args):
        yield tmp_path / "fake-input"

    def focus(*args):
        state["focus_checks"] += 1
        if state["focus_checks"] == 2:
            state["cursor"] = (1600, 500)
        return target["address"]

    monkeypatch.setattr(native_input, "temporary_input", input_socket)
    monkeypatch.setattr(native_input, "focused_window", focus)
    monkeypatch.setattr(native_input, "capture_dialog", lambda *args: button)
    monkeypatch.setattr(native_input, "current_target", lambda *args: target)
    monkeypatch.setattr(native_input, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(
        native_input,
        "move_cursor",
        lambda configuration, position: state.update(cursor=position),
    )
    monkeypatch.setattr(
        native_input.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("clicked after user moved"),
    )
    with pytest.raises(RuntimeError, match="cursor changed after movement"):
        native_input.click_once({}, target, button, tmp_path, (10, 20))
    assert state["cursor"] == (1600, 500)
