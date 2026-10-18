import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_devtools_session as sessions


def test_manual_scope_is_not_automatically_cleaned(tmp_path, monkeypatch):
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    assert not sessions.ChromeDevtoolsSession.current(tmp_path).automatic_cleanup


def test_codex_thread_owns_a_scope_without_herdr(tmp_path, monkeypatch):
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-one")
    first = sessions.ChromeDevtoolsSession.current(tmp_path)
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-two")
    second = sessions.ChromeDevtoolsSession.current(tmp_path)
    assert first.automatic_cleanup
    assert first.identifier != second.identifier


def test_pid_file_matches_upstream_linux_and_darwin_locations(tmp_path, monkeypatch):
    session = sessions.ChromeDevtoolsSession("abc123", tmp_path, True)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    assert session.pid_file == tmp_path / "chrome-devtools-mcp-abc123/daemon.pid"
    monkeypatch.delenv("XDG_RUNTIME_DIR")
    monkeypatch.setattr(sessions.os, "getuid", lambda: 42)
    assert session.pid_file.parts == (
        "/",
        "tmp",
        "chrome-devtools-mcp-abc123-42",
        "daemon.pid",
    )


@pytest.mark.parametrize("content", ["invalid", "0", "-1"])
def test_invalid_pid_never_targets_a_process(tmp_path, monkeypatch, content):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    session = sessions.ChromeDevtoolsSession("abc123", tmp_path, True)
    session.pid_file.parent.mkdir()
    session.pid_file.write_text(content)
    monkeypatch.setattr(
        sessions.os, "kill", lambda *arguments: pytest.fail("signaled a process")
    )
    assert not session.running()


def test_corrupt_mode_falls_back_to_attached_profile(tmp_path):
    session = sessions.ChromeDevtoolsSession("abc123", tmp_path, True)
    session.state_file.write_text("{invalid")
    assert session.mode() == "attached"
