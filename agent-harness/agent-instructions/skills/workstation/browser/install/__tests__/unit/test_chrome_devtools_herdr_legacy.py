import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_target as target
import chrome_devtools_command as command
from chrome_devtools_session import ChromeDevtoolsSession


@pytest.fixture
def contexts(tmp_path, monkeypatch):
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_SESSION", "alpha")
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "alpha/herdr.sock"))
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    current = ChromeDevtoolsSession.current(tmp_path)
    identifier = hashlib.sha256(b"HERDR_PANE_ID:w1:p2").hexdigest()[:32]
    legacy = ChromeDevtoolsSession(identifier, current.directory, True)
    legacy.record_mode("headless", "/current/backend")
    legacy.pid_file.parent.mkdir(parents=True)
    legacy.pid_file.write_text(str(os.getpid()))
    token = legacy.directory / legacy.identifier / ("consent-" + "a" * 32 + ".json")
    token.parent.mkdir()
    token.write_text('{"expires":0}')
    paths = (legacy.state_file, legacy.pid_file, token)
    snapshot = {path: path.read_bytes() for path in paths}
    configuration = command.ChromeDevtoolsConfiguration(
        "/current/backend", tmp_path, "/ffmpeg", "/chrome"
    )
    return current, legacy, snapshot, configuration


def unchanged(snapshot):
    assert all(path.read_bytes() == contents for path, contents in snapshot.items())


def test_live_legacy_worker_cannot_be_reused_or_migrated(contexts, monkeypatch):
    current, legacy, snapshot, configuration = contexts
    assert legacy.running()
    assert not current.running()
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("touched a legacy worker"),
    )
    with pytest.raises(RuntimeError, match="requires scoped approval"):
        command.main(configuration, ["connect", "--timeout", "3"])
    assert not current.state_file.exists()
    assert current.mode() == "attached"
    unchanged(snapshot)


@pytest.mark.parametrize("operation", ["cleanup", "stop"])
def test_cleanup_never_stops_or_deletes_legacy_shared_state(
    contexts, monkeypatch, operation
):
    current, legacy, snapshot, configuration = contexts
    calls = []
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda arguments, **kwargs: calls.append(arguments)
        or SimpleNamespace(returncode=0),
    )
    assert command.main(configuration, [operation]) == 0
    assert calls == (
        []
        if operation == "cleanup"
        else [["/current/backend", "--sessionId", current.identifier, "stop"]]
    )
    unchanged(snapshot)


def test_cleanup_in_one_named_session_preserves_other_session(contexts, monkeypatch):
    first, legacy, snapshot, configuration = contexts
    first.record_mode("attached", "/current/backend")
    first_token = first.directory / first.identifier / "consent-owned.json"
    first_token.parent.mkdir()
    first_token.write_text("other session token")
    monkeypatch.setenv("HERDR_SESSION", "beta")
    second = ChromeDevtoolsSession.current(configuration.home_directory)
    second.record_mode("headless", "/current/backend")
    monkeypatch.setattr(
        command.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )
    assert command.main(configuration, ["cleanup"]) == 0
    assert (
        first.state_file.exists() and first_token.read_text() == "other session token"
    )
    assert not second.state_file.exists()
    unchanged(snapshot)


def test_preparation_prunes_only_the_new_namespace(contexts, monkeypatch, capsys):
    current, legacy, snapshot, configuration = contexts
    window = {
        "address": "chrome",
        "pid": 1,
        "process_start": "2",
        "at": [0, 0],
        "size": [1920, 1080],
    }
    monkeypatch.setattr(target, "current_target", lambda *args: window)
    target.prepare({}, current.directory / current.identifier)
    token = json.loads(capsys.readouterr().out)["token"]
    (current.directory / current.identifier / f"consent-{token}.json").unlink()
    unchanged(snapshot)
