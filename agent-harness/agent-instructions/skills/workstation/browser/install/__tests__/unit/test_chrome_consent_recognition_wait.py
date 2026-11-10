import csv
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_dialog as dialog
import chrome_consent_helper as helper


@pytest.fixture
def recognition_frames(monkeypatch):
    path = (
        Path(__file__).resolve().parents[1]
        / "fixtures/native-consent-current-warning.tsv"
    )
    with path.open() as stream:
        words = list(csv.DictReader(stream, delimiter="\t"))
    clock = [0.0]

    def advance(duration):
        clock[0] += duration

    monkeypatch.setattr(
        helper, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=advance)
    )
    monkeypatch.setattr(helper, "verify_unchanged_attempt", Mock())
    return words, clock


def uncertain_frame(words, failure):
    changed = [dict(word) for word in words]
    changed[5]["text" if failure == "text" else "conf"] = (
        "unreadable" if failure == "text" else "74"
    )
    return changed


@pytest.mark.parametrize("failure", ["text", "confidence"])
@pytest.mark.parametrize("stage", ["capture", "revalidation"])
def test_fresh_dialog_waits_for_exact_recognition(
    recognition_frames, monkeypatch, tmp_path, failure, stage
):
    words, clock = recognition_frames
    attempts = {"capture": 0, "revalidation": 0}
    clicks = []

    def capture(*args):
        attempts["capture"] += 1
        if stage == "capture" and attempts["capture"] == 1:
            return dialog.find_allow_button(
                uncertain_frame(words, failure), (1916, 1076)
            )
        return dialog.find_allow_button(words, (1916, 1076))

    def click(*args):
        attempts["revalidation"] += 1
        if stage == "revalidation" and attempts["revalidation"] == 1:
            dialog.verify_warning(uncertain_frame(words, failure))
        clicks.append(args[2].position)

    monkeypatch.setattr(helper, "capture_dialog", capture)
    monkeypatch.setattr(helper, "click_once", click)
    helper.await_consent({}, {}, tmp_path, (0, 0), 0.3)
    assert clicks == [(1118, 278)]
    assert clock[0] == pytest.approx(0.1)


@pytest.mark.parametrize("failure", ["text", "confidence"])
def test_unrecognized_fresh_dialog_expires_without_click(
    recognition_frames, monkeypatch, tmp_path, failure
):
    words, clock = recognition_frames
    click = Mock()
    monkeypatch.setattr(
        helper,
        "capture_dialog",
        lambda *args: dialog.find_allow_button(
            uncertain_frame(words, failure), (1916, 1076)
        ),
    )
    monkeypatch.setattr(helper, "click_once", click)
    with pytest.raises(RuntimeError, match="deadline"):
        helper.await_consent({}, {}, tmp_path, (0, 0), 0.3)
    click.assert_not_called()
    assert clock[0] >= 0.3


@pytest.mark.parametrize("failure", ["text", "confidence"])
def test_unrecognized_existing_dialog_never_arms(
    recognition_frames, monkeypatch, tmp_path, failure
):
    words, clock = recognition_frames
    monkeypatch.setattr(
        helper,
        "capture_dialog",
        lambda *args: dialog.find_allow_button(
            uncertain_frame(words, failure), (1916, 1076)
        ),
    )
    with pytest.raises(RuntimeError):
        helper.prepare_watch({}, {}, tmp_path, (0, 0))
    assert clock[0] == 0


def test_safety_failure_is_not_a_recognition_retry(
    recognition_frames, monkeypatch, tmp_path
):
    _, clock = recognition_frames
    capture = Mock(side_effect=RuntimeError("Chrome process changed"))
    monkeypatch.setattr(helper, "capture_dialog", capture)
    with pytest.raises(RuntimeError, match="process changed"):
        helper.await_consent({}, {}, tmp_path, (0, 0), 0.3)
    capture.assert_called_once()
    assert clock[0] == 0
