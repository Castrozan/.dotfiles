import json
from pathlib import Path

import pytest

from codex_daemon import DaemonLease


@pytest.fixture(autouse=True)
def native_process_record(tmp_path):
    (tmp_path / "app-server-daemon").mkdir()
    (tmp_path / "app-server-daemon/daemon.pid").write_text(json.dumps({"pid": 42}))


def daemon_result(status="started", running="1", installed="1"):
    return {
        "status": status,
        "pid": 42,
        "appServerVersion": running,
        "cliVersion": installed,
        "socketPath": "/tmp/daemon.sock",
    }


def test_daemon_start_scrubs_client_markers_and_reuses_its_owned_process(
    tmp_path, monkeypatch
):
    lease = DaemonLease(
        "codex",
        {
            "CODEX_HOME": str(tmp_path),
            "HERDR_PANE_ID": "wrong",
            "PATH": "bin",
            "API_KEY": "secret",
        },
    )
    results = iter([daemon_result(), daemon_result("alreadyRunning")])
    monkeypatch.setattr(lease, "command", lambda operation: next(results))
    try:
        assert lease.ensure_running() == Path("/tmp/daemon.sock")
        assert lease.ensure_running() == Path("/tmp/daemon.sock")
        assert lease.environment == {
            "CODEX_HOME": str(tmp_path),
            "PATH": "bin",
            "DOTFILES_CODEX_SHARED_SERVER": "1",
        }
    finally:
        lease.close()


def test_unowned_running_daemon_is_not_silently_adopted(tmp_path, monkeypatch):
    lease = DaemonLease("codex", {"CODEX_HOME": str(tmp_path)})
    monkeypatch.setattr(
        lease, "command", lambda operation: daemon_result("alreadyRunning")
    )
    try:
        with pytest.raises(RuntimeError, match="outside the client adapter"):
            lease.ensure_running()
    finally:
        lease.close()


def test_upgrade_preserves_attached_clients_then_restarts_after_they_exit(
    tmp_path, monkeypatch
):
    first = DaemonLease("codex", {"CODEX_HOME": str(tmp_path)})
    second = DaemonLease("codex", {"CODEX_HOME": str(tmp_path)})
    (first.directory / "daemon.json").write_text(json.dumps({"pid": 42}))
    operations = []

    def command(operation):
        operations.append(operation)
        return (
            daemon_result("alreadyRunning", "1", "2")
            if operation == "start"
            else daemon_result(installed="2", running="2")
        )

    monkeypatch.setattr(second, "command", command)
    try:
        with pytest.raises(RuntimeError, match="upgraded while shared clients"):
            second.ensure_running()
        assert operations == ["start"]
        first.close()
        second.ensure_running()
        assert operations == ["start", "start", "restart"]
    finally:
        if not first.clients.closed:
            first.close()
        second.close()
