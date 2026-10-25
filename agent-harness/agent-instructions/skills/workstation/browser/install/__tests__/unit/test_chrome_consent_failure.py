from contextlib import contextmanager
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_helper as helper
import chrome_consent_input as native_input
from chrome_consent_dialog import DialogButton


@pytest.mark.parametrize("changed,dialog", [(False, True), (False, None), (True, True)])
def test_failed_attempt_dismisses_only_its_fresh_dialog(
    tmp_path, monkeypatch, changed, dialog
):
    keys = []

    def unchanged(*args):
        if changed:
            raise RuntimeError("User moved")

    monkeypatch.setattr(helper, "verify_unchanged_attempt", unchanged)
    monkeypatch.setattr(helper, "capture_dialog", lambda *args, **kwargs: dialog)
    monkeypatch.setattr(
        helper.subprocess, "run", lambda args, **kwargs: keys.append(args)
    )
    helper.dismiss_failed_attempt({"wtype": "fake-wtype"}, {}, tmp_path, (10, 20))
    assert keys == ([["fake-wtype", "-k", "Escape"]] if dialog and not changed else [])


def test_watch_failure_dismisses_before_restoring_view(tmp_path, monkeypatch):
    events = []
    monkeypatch.setattr(helper, "consume_token", lambda *args: {})
    monkeypatch.setattr(helper, "prepare_watch", lambda *args: None)

    @contextmanager
    def view(*args):
        try:
            yield {}, (10, 20)
        finally:
            events.append("restore")

    def failed(*args):
        raise RuntimeError("request cancelled")

    monkeypatch.setattr(helper, "focused_view", view)
    monkeypatch.setattr(helper, "await_consent", failed)
    monkeypatch.setattr(
        helper, "dismiss_failed_attempt", lambda *args: events.append("dismiss")
    )
    with pytest.raises(RuntimeError, match="request cancelled"):
        helper.watch({}, tmp_path, "token", 1)
    assert events == ["dismiss", "restore"]


def test_geometry_movement_after_pointer_move_prevents_click(tmp_path, monkeypatch):
    target = {
        "address": "chrome",
        "pid": 123,
        "process_start": "456",
        "at": [2, 2],
        "size": [1916, 1076],
    }
    button = DialogButton((1119, 285), (744, 52, 1184, 311))
    state = {"cursor": (42, 22), "target_reads": 0}

    @contextmanager
    def input_socket(*args):
        yield tmp_path / "input"

    def observed(*args):
        state["target_reads"] += 1
        return target if state["target_reads"] == 1 else {**target, "at": [2, 100]}

    monkeypatch.setattr(native_input, "temporary_input", input_socket)
    monkeypatch.setattr(native_input, "focused_window", lambda *args: "chrome")
    monkeypatch.setattr(native_input, "capture_dialog", lambda *args: button)
    monkeypatch.setattr(native_input, "current_target", observed)
    monkeypatch.setattr(native_input, "cursor_position", lambda *args: state["cursor"])
    monkeypatch.setattr(
        native_input,
        "move_cursor",
        lambda configuration, position: state.update(cursor=position),
    )
    monkeypatch.setattr(
        native_input.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("clicked stale geometry"),
    )
    with pytest.raises(RuntimeError, match="geometry changed after cursor movement"):
        native_input.click_once({}, target, button, tmp_path, (42, 22))
    assert state["cursor"] == (42, 22)
