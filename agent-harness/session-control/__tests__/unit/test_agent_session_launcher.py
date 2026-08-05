from pathlib import Path
from types import SimpleNamespace

from agent_session import relaunch, restart_lock


def test_prepared_restart_launcher_returns_its_process_identifier(monkeypatch):
    closed_file_descriptors = []
    monkeypatch.setattr(relaunch.os, "pipe", lambda: (31, 32))
    monkeypatch.setattr(relaunch.os, "close", closed_file_descriptors.append)
    monkeypatch.setattr(
        relaunch.subprocess,
        "Popen",
        lambda *_arguments, **_keywords: SimpleNamespace(pid=104),
    )
    monkeypatch.setattr(
        relaunch,
        "restart_launcher_is_ready",
        lambda _file_descriptor: True,
    )

    assert (
        relaunch.launch_restart_launcher(
            102,
            "herdr",
            "pane-123",
            ["codex", "resume", "session-123"],
            restart_lock.RestartLock(
                Path("/tmp/agent-session-restart-102.lock"), "token"
            ),
        )
        == 104
    )
    assert closed_file_descriptors == [32, 31]


def test_unready_restart_launcher_is_terminated_and_reaped(monkeypatch):
    closed_file_descriptors = []
    process_group_signals = []
    launcher_waits = []
    launched_process = SimpleNamespace(
        pid=104,
        wait=lambda timeout=None: launcher_waits.append(timeout),
    )
    monkeypatch.setattr(relaunch.os, "pipe", lambda: (31, 32))
    monkeypatch.setattr(relaunch.os, "close", closed_file_descriptors.append)
    monkeypatch.setattr(
        relaunch.os,
        "killpg",
        lambda process_identifier, signal: process_group_signals.append(
            (process_identifier, signal)
        ),
        raising=False,
    )
    monkeypatch.setattr(
        relaunch.subprocess,
        "Popen",
        lambda *_arguments, **_keywords: launched_process,
    )
    monkeypatch.setattr(
        relaunch,
        "restart_launcher_is_ready",
        lambda _file_descriptor: False,
    )

    assert (
        relaunch.launch_restart_launcher(
            102,
            "herdr",
            "pane-123",
            ["codex", "resume", "session-123"],
            restart_lock.RestartLock(
                Path("/tmp/agent-session-restart-102.lock"), "token"
            ),
        )
        is None
    )
    assert process_group_signals == [(104, relaunch.signal.SIGTERM)]
    assert launcher_waits
    assert closed_file_descriptors == [32, 31]


def test_failed_restart_launcher_closes_both_pipe_file_descriptors(monkeypatch):
    closed_file_descriptors = []
    monkeypatch.setattr(relaunch.os, "pipe", lambda: (31, 32))
    monkeypatch.setattr(
        relaunch.os,
        "close",
        closed_file_descriptors.append,
    )
    monkeypatch.setattr(
        relaunch.subprocess,
        "Popen",
        lambda *_arguments, **_keywords: (_ for _ in ()).throw(OSError("failed")),
    )

    assert not relaunch.launch_restart_launcher(
        102,
        "herdr",
        "pane-123",
        ["codex", "resume", "session-123"],
        restart_lock.RestartLock(Path("/tmp/agent-session-restart-102.lock"), "token"),
    )
    assert closed_file_descriptors == [32, 31]
