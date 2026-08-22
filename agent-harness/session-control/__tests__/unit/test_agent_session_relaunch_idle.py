import os
from argparse import Namespace
from types import SimpleNamespace

import pytest

from agent_session import relaunch, relaunch_transport, restart_lock


def test_reads_the_herdr_foreground_process_identifiers(monkeypatch):
    monkeypatch.setattr(
        relaunch_transport.subprocess,
        "run",
        lambda *_arguments, **_keywords: SimpleNamespace(
            returncode=0,
            stdout=(
                '{"result":{"process_info":{"foreground_process_group_id":102,'
                '"shell_pid":101,"foreground_processes":[{"pid":102}]}}}'
            ),
        ),
    )

    assert relaunch_transport.herdr_pane_foreground_process_identifiers("pane-123") == {
        102
    }
    assert not relaunch_transport.herdr_pane_is_idle("pane-123")


def test_relaunch_waits_for_a_herdr_pane_to_return_to_its_shell(monkeypatch, tmp_path):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock,
        "restart_lock_path_for",
        lambda _process_identifier: lock_path,
    )
    acquired_restart_lock = restart_lock.acquire_restart_lock(102)
    assert acquired_restart_lock is not None
    ready_reader_file_descriptor, ready_writer_file_descriptor = os.pipe()
    idle_waits = []
    monkeypatch.setattr(relaunch, "relaunch_target_is_ready", lambda *_arguments: True)
    monkeypatch.setattr(
        relaunch, "wait_for_agent_session_exit", lambda _process_identifier: True
    )
    monkeypatch.setattr(
        relaunch,
        "wait_for_relaunch_target_idle",
        lambda *arguments: idle_waits.append(arguments) or False,
        raising=False,
    )
    monkeypatch.setattr(
        relaunch_transport.subprocess,
        "run",
        lambda *_arguments, **_keywords: pytest.fail(
            "must not relaunch into a busy pane"
        ),
    )

    try:
        assert (
            relaunch.relaunch_after_exit(
                Namespace(
                    process_identifier=102,
                    multiplexer_name="herdr",
                    pane_identifier="pane-123",
                    resume_command='["codex", "resume", "session-123"]',
                    restart_lock_path=str(lock_path),
                    restart_lock_owner_token=acquired_restart_lock.owner_token,
                    restart_launcher_ready_file_descriptor=ready_writer_file_descriptor,
                )
            )
            == 1
        )
        assert idle_waits == [("herdr", "pane-123")]
    finally:
        os.close(ready_reader_file_descriptor)
        os.close(ready_writer_file_descriptor)
