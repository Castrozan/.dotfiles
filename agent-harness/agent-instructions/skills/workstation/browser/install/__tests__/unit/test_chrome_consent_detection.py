import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_dialog as dialog


def native_warning_words():
    path = Path(__file__).resolve().parents[1] / "fixtures/native-consent-warning.tsv"
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_captured_native_warning_identifies_only_allow():
    button = dialog.find_allow_button(native_warning_words(), (1916, 1076))
    assert button.position == (1119, 285)


@pytest.mark.parametrize(
    "change",
    [
        "relocated_allow",
        "relocated_cancel",
        "empty_button",
        "nan",
        "infinite",
        "overconfident",
        "low_confidence",
        "missing_text",
        "duplicate_allow",
        "duplicate_title",
    ],
)
def test_distractors_and_ambiguous_controls_are_rejected(change):
    words = native_warning_words()
    if change == "relocated_allow":
        words[-1]["left"] = "800"
    elif change == "relocated_cancel":
        words[-2]["left"] = "1100"
    elif change == "empty_button":
        words[-1]["width"] = "0"
    elif change in ("nan", "infinite", "overconfident", "low_confidence"):
        words[-1]["conf"] = {
            "nan": "NaN",
            "infinite": "inf",
            "overconfident": "101",
            "low_confidence": "70",
        }[change]
    elif change == "missing_text":
        words.pop(10)
    elif change == "duplicate_allow":
        words.append(dict(words[-1]))
    else:
        words.extend({**w, "block_num": "99"} for w in words[:3])
    with pytest.raises(RuntimeError):
        dialog.find_allow_button(words, (1916, 1076))


def test_allow_elsewhere_in_page_is_never_selected():
    words = native_warning_words()
    words.append({**words[-1], "top": "500", "line_num": "99"})
    assert dialog.find_allow_button(words, (1916, 1076)).position == (1119, 285)


def test_absent_dialog_is_not_an_allow_target():
    assert dialog.find_allow_button([], (1916, 1076)) is None


def test_scaled_capture_is_rejected_before_recognition(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace

    @contextmanager
    def image(*args):
        yield SimpleNamespace(size=(3832, 2152))

    monkeypatch.setitem(
        sys.modules, "PIL", SimpleNamespace(Image=SimpleNamespace(open=image))
    )
    monkeypatch.setattr(dialog.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        dialog,
        "inspect_image",
        lambda *args: pytest.fail("recognized unsupported scaled pixels"),
    )
    with pytest.raises(RuntimeError, match="Scaled display"):
        dialog.capture_dialog(
            {"grim": "fake-grim"}, {"at": [2, 2], "size": [1916, 1076]}, tmp_path
        )
