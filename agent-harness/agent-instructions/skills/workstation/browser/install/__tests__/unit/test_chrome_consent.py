import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_dialog as dialog
import chrome_consent_helper as helper
import chrome_consent_target as target


def warning_words():
    lines = [
        "Allow remote debugging?",
        "An external app wants full control over this Chrome",
        "session to debug it. This includes access to your",
        "saved data, cookies and site data, and the ability to",
        "navigate to any URL.",
        "Only web developers should turn on this feature, and",
        "only use it with trusted apps.",
        "Turn off in settings Cancel Allow",
    ]
    words = []
    for index, line in enumerate(lines):
        x = 750
        for text in line.split():
            words.append(
                {
                    "text": text,
                    "left": x,
                    "top": 70 + index * 30,
                    "width": len(text) * 6,
                    "height": 12,
                    "conf": "95",
                    "block_num": "1",
                    "par_num": "1",
                    "line_num": str(index),
                }
            )
            x += len(text) * 6 + 5
    return words


def test_exact_warning_has_only_one_allow_target():
    button = dialog.find_allow_button(warning_words(), (1920, 1080))
    assert button is not None
    assert button.position[1] == 286


@pytest.mark.parametrize("change", ["body", "location", "confidence", "duplicate"])
def test_ambiguous_or_changed_warning_fails_closed(change):
    words = warning_words()
    if change == "body":
        words[8]["text"] = "different"
    elif change == "location":
        for word in words:
            word["top"] += 300
    elif change == "confidence":
        words[4]["conf"] = "30"
    else:
        words.extend({**word, "block_num": "2"} for word in words[:3])
    with pytest.raises(RuntimeError):
        dialog.find_allow_button(words, (1920, 1080))


def test_missing_dialog_never_produces_coordinates():
    assert dialog.find_allow_button([], (1920, 1080)) is None


@pytest.fixture
def prepared_token(tmp_path, monkeypatch):
    window = {
        "address": "0x123",
        "pid": 123,
        "process_start": "456",
        "at": [0, 0],
        "size": [1920, 1080],
    }
    monkeypatch.setattr(target, "current_target", lambda configuration: window)
    monkeypatch.setattr(helper, "move_cursor", lambda *args: None)
    monkeypatch.setattr(helper, "dismiss_failed_attempt", lambda *args: None)
    target.prepare({}, tmp_path)
    path = next(tmp_path.glob("consent-*.json"))
    return tmp_path, path, path.stem.removeprefix("consent-"), window


def test_token_is_single_use_and_private(prepared_token):
    directory, path, token, window = prepared_token
    assert path.stat().st_mode & 0o777 == 0o600
    assert target.consume_token({}, directory, token) == window
    with pytest.raises(FileNotFoundError):
        target.consume_token({}, directory, token)


@pytest.mark.parametrize("change", ["expired", "process", "geometry"])
def test_expired_or_changed_target_consumes_token_without_approval(
    prepared_token, change
):
    directory, path, token, window = prepared_token
    if change == "expired":
        record = json.loads(path.read_text())
        record["expires"] = 0
        path.write_text(json.dumps(record))
    elif change == "process":
        window["process_start"] = "different"
    else:
        window["at"] = [1, 1]
    with pytest.raises(RuntimeError):
        target.consume_token({}, directory, token)
    assert not path.exists()


def test_existing_dialog_is_never_approved(prepared_token, monkeypatch):
    directory, path, token, window = prepared_token
    monkeypatch.setattr(helper, "consume_token", lambda *args: window)
    monkeypatch.setattr(helper, "focused_window", lambda *args: window["address"])
    positions = iter([(10, 20), (40, 20)])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: next(positions))
    monkeypatch.setattr(helper, "focus_window", lambda *args: None)
    monkeypatch.setattr(helper, "capture_dialog", lambda *args: object())
    monkeypatch.setattr(
        helper, "click_once", lambda *args: pytest.fail("clicked a pre-existing dialog")
    )
    with pytest.raises(RuntimeError, match="predates"):
        helper.watch({}, directory, token, 1)


def test_user_focus_change_aborts_and_does_not_restore_over_user(
    prepared_token, monkeypatch
):
    directory, path, token, window = prepared_token
    focus = iter(["0xoriginal", window["address"], "0xuser", "0xuser"])
    focused = []
    monkeypatch.setattr(helper, "consume_token", lambda *args: window)
    monkeypatch.setattr(helper, "focused_window", lambda *args: next(focus))
    positions = iter([(10, 20), (40, 20)])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: next(positions))
    monkeypatch.setattr(
        helper, "focus_window", lambda configuration, address: focused.append(address)
    )
    monkeypatch.setattr(helper, "capture_dialog", lambda *args: None)
    monkeypatch.setattr(
        helper,
        "click_once",
        lambda *args: pytest.fail("clicked after user changed focus"),
    )
    with pytest.raises(RuntimeError, match="User focus"):
        helper.watch({}, directory, token, 1)
    assert focused == [window["address"]]


def test_missing_dialog_times_out_without_click_and_restores_focus(
    prepared_token, monkeypatch
):
    directory, path, token, window = prepared_token
    focused = []
    focus = iter(["0xoriginal", window["address"], window["address"]])
    monkeypatch.setattr(helper, "consume_token", lambda *args: window)
    monkeypatch.setattr(helper, "focused_window", lambda *args: next(focus))
    positions = iter([(10, 20), (40, 20)])
    monkeypatch.setattr(helper, "cursor_position", lambda *args: next(positions))
    monkeypatch.setattr(
        helper, "focus_window", lambda configuration, address: focused.append(address)
    )
    monkeypatch.setattr(helper, "capture_dialog", lambda *args: None)
    monkeypatch.setattr(
        helper, "click_once", lambda *args: pytest.fail("clicked without a dialog")
    )
    with pytest.raises(RuntimeError, match="deadline"):
        helper.watch({}, directory, token, 0)
    assert focused == [window["address"], "0xoriginal"]
