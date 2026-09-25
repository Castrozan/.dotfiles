import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor")
)

import import_repair


@pytest.mark.parametrize("payload", [None, {"name": "ManualImport"}])
def test_request_transport_has_bounded_timeout(monkeypatch, payload):
    calls = []
    monkeypatch.setattr(
        import_repair,
        "http_request",
        lambda *args, **kwargs: calls.append((args, kwargs)) or (200, "{}"),
    )
    assert import_repair.request_json("http://arr", "key", "command", payload) == {}
    assert calls[0][1]["timeout_seconds"] == 5
    assert calls[0][0][0] == ("GET" if payload is None else "POST")


def test_request_failure_is_not_treated_as_import_success(monkeypatch):
    monkeypatch.setattr(
        import_repair, "http_request", lambda *args, **kwargs: (401, "denied")
    )
    with pytest.raises(ValueError, match="HTTP 401"):
        import_repair.request_json("http://arr", "key", "command")


def test_unwritable_state_cannot_interrupt_supervisor(monkeypatch):
    monkeypatch.setattr(import_repair, "read_last_active_epoch", lambda path: None)

    def fail(*args):
        raise PermissionError("read only")

    monkeypatch.setattr(import_repair, "write_last_active_epoch", fail)
    import_repair.maybe_repair_blocked_imports(
        {"state_file_path": "/state/activity"}, 1000, False
    )
