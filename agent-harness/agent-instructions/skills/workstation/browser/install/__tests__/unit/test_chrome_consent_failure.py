from contextlib import contextmanager
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_helper as helper


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
