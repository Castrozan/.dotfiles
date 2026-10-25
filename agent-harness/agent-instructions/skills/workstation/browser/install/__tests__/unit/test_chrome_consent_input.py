import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_helper as helper
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
    positions = iter([(10, 20), button.position])
    monkeypatch.setattr(helper.subprocess, "Popen", lambda *args, **kwargs: daemon)
    monkeypatch.setattr(helper, "stop_process", lambda process: stopped.append(process))
    monkeypatch.setattr(Path, "exists", lambda self: self.name == "ydotool.sock")
    monkeypatch.setattr(helper, "focused_window", lambda *args: target["address"])
    monkeypatch.setattr(
        helper, "capture_dialog", lambda *args: None if changed else button
    )
    monkeypatch.setattr(helper, "current_target", lambda *args: target)
    monkeypatch.setattr(helper, "cursor_position", lambda *args: next(positions))
    monkeypatch.setattr(
        helper, "move_cursor", lambda configuration, position: moved.append(position)
    )
    monkeypatch.setattr(
        helper.subprocess, "run", lambda arguments, **kwargs: clicks.append(arguments)
    )
    if changed:
        with pytest.raises(RuntimeError, match="changed before"):
            helper.click_once(
                {"ydotoold": "daemon", "ydotool": "input"},
                target,
                button,
                tmp_path,
                (10, 20),
            )
        assert not clicks
        assert not moved
    else:
        helper.click_once(
            {"ydotoold": "daemon", "ydotool": "input"},
            target,
            button,
            tmp_path,
            (10, 20),
        )
        assert clicks == [["input", "click", "0xC0"]]
        assert moved == [button.position, (10, 20)]
    assert stopped == [daemon]
