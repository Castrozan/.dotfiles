from argparse import Namespace
from pathlib import Path

import pytest

from agent_session import control, restart_lock


def test_uses_its_own_parent_even_when_the_test_override_is_set(monkeypatch):
    monkeypatch.setenv("AGENT_SESSION_ANCESTOR_SCAN_START_PROCESS_ID", "999")
    monkeypatch.setattr(control.os, "getppid", lambda: 102)

    assert control.starting_process_identifier() == 102


def test_restart_relaunches_the_detected_harness_after_its_current_process_exits(
    monkeypatch,
):
    terminated_processes = []
    acquired_restart_lock = restart_lock.RestartLock(
        Path("/tmp/agent-session-restart-102.lock"), "owner-token"
    )
    monkeypatch.setattr(
        control,
        "agent_session_from_current_process",
        lambda: (102, "codex", "codex resume session-123"),
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
        raising=False,
    )
    monkeypatch.setattr(
        control,
        "process_is_descendant_of",
        lambda process_identifier, ancestor_process_identifier: process_identifier
        == ancestor_process_identifier,
        raising=False,
    )
    monkeypatch.setattr(
        control.restart_lock,
        "acquire_restart_lock",
        lambda _process_identifier: acquired_restart_lock,
    )
    monkeypatch.setattr(
        control,
        "launch_restart_launcher",
        lambda *arguments: 104
        if arguments
        == (
            102,
            "herdr",
            "pane-123",
            ["codex", "resume", "session-123"],
            acquired_restart_lock,
        )
        else None,
    )
    monkeypatch.setattr(control.os, "getpid", lambda: 103)
    monkeypatch.setattr(
        control,
        "terminate_agent_session",
        lambda *arguments: terminated_processes.append(arguments),
    )

    assert control.restart_current_agent_session(Namespace()) == 0
    assert terminated_processes == [(102, frozenset({103, 104}))]


def test_restart_refuses_to_bypass_a_clawde_wrapper(monkeypatch, capsys):
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "steward")
    monkeypatch.setattr(
        control,
        "agent_session_from_current_process",
        lambda: pytest.fail("must stop before inspecting the wrapped harness"),
    )

    assert control.restart_current_agent_session(Namespace()) == 1
    assert "Clawde-managed" in capsys.readouterr().out


def test_restart_refuses_a_clawde_wrapper_even_without_its_environment_marker(
    monkeypatch, capsys
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setattr(control.os, "getppid", lambda: 101)
    monkeypatch.setattr(
        control,
        "clawde_wrapper_is_ancestor_of",
        lambda _process_identifier: True,
        raising=False,
    )
    monkeypatch.setattr(
        control,
        "agent_session_from_current_process",
        lambda: pytest.fail("must stop before inspecting the wrapped harness"),
    )

    assert control.restart_current_agent_session(Namespace()) == 1
    assert "Clawde-managed" in capsys.readouterr().out


def test_restart_refuses_a_pane_that_does_not_contain_the_agent_session(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        control,
        "agent_session_from_current_process",
        lambda: (102, "codex", "codex resume session-123"),
    )
    monkeypatch.setattr(
        control,
        "multiplexer_context_from_environment",
        lambda: ("herdr", "pane-123"),
    )
    monkeypatch.setattr(
        control,
        "herdr_pane_foreground_process_identifiers",
        lambda _pane_identifier: {999},
        raising=False,
    )
    monkeypatch.setattr(
        control,
        "process_is_descendant_of",
        lambda *_arguments: False,
        raising=False,
    )
    monkeypatch.setattr(
        control,
        "launch_restart_launcher",
        lambda *_arguments: pytest.fail("must not launch into another pane"),
    )

    assert control.restart_current_agent_session(Namespace()) == 1
    assert "does not contain" in capsys.readouterr().out
