from argparse import Namespace
from pathlib import Path

import pytest

from agent_session import control, restart_lock


def configure_fresh_codex_restart(monkeypatch, reported_session_identifier):
    resume_commands = []
    terminated_processes = []
    acquired_restart_lock = restart_lock.RestartLock(
        Path("/tmp/agent-session-restart-102.lock"), "owner-token"
    )
    monkeypatch.setattr(
        control,
        "agent_session_from_current_process",
        lambda: (102, "codex", "codex --no-alt-screen"),
    )
    monkeypatch.setattr(
        control,
        "multiplexer_context_from_environment",
        lambda: ("herdr", "pane-123"),
    )
    monkeypatch.setattr(
        control,
        "herdr_pane_foreground_process_identifiers",
        lambda _pane_identifier: {102},
    )
    monkeypatch.setattr(
        control,
        "process_is_descendant_of",
        lambda process_identifier, ancestor_process_identifier: process_identifier
        == ancestor_process_identifier,
    )
    monkeypatch.setattr(
        control,
        "herdr_pane_agent_session_identifier",
        lambda _pane_identifier, _harness_name: reported_session_identifier,
    )
    monkeypatch.setattr(
        control.restart_lock,
        "acquire_restart_lock",
        lambda _process_identifier: acquired_restart_lock,
    )
    monkeypatch.setattr(
        control,
        "launch_restart_launcher",
        lambda _process_identifier,
        _multiplexer_name,
        _pane_identifier,
        resume_command,
        _restart_lock: resume_commands.append(resume_command) or 104,
    )
    monkeypatch.setattr(control.os, "getpid", lambda: 103)
    monkeypatch.setattr(
        control,
        "terminate_agent_session",
        lambda *arguments: terminated_processes.append(arguments),
    )
    return resume_commands, terminated_processes


def test_restart_uses_the_current_panes_reported_codex_session(monkeypatch):
    resume_commands, terminated_processes = configure_fresh_codex_restart(
        monkeypatch, "session-456"
    )

    assert control.restart_current_agent_session(Namespace()) == 0
    assert resume_commands == [["codex", "resume", "session-456"]]
    assert terminated_processes == [(102, frozenset({103, 104}))]


def test_restart_preserves_the_session_when_herdr_has_no_identifier(
    monkeypatch, capsys
):
    resume_commands, terminated_processes = configure_fresh_codex_restart(
        monkeypatch, None
    )
    monkeypatch.setattr(
        control.restart_lock,
        "acquire_restart_lock",
        lambda _process_identifier: pytest.fail("must resolve identity before locking"),
    )

    assert control.restart_current_agent_session(Namespace()) == 1
    assert "could not resolve" in capsys.readouterr().out
    assert resume_commands == []
    assert terminated_processes == []
