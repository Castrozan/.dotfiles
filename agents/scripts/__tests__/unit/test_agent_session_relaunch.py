import os
from argparse import Namespace

import pytest

from agent_session import relaunch, relaunch_transport, restart_lock


def test_builds_herdr_relaunch_commands_without_bracketed_paste():
    assert relaunch_transport.relaunch_commands_for(
        "herdr", "pane-123", ["codex", "resume", "--last"]
    ) == [
        ["herdr", "agent", "send", "pane-123", "codex resume --last"],
        ["herdr", "pane", "send-keys", "pane-123", "Enter"],
    ]


def test_relaunch_refuses_a_lock_path_that_does_not_belong_to_the_agent_session(
    monkeypatch, tmp_path
):
    unrelated_lock_path = tmp_path / "agent-session-restart-103.lock"
    unrelated_lock_path.touch()
    monkeypatch.setattr(
        restart_lock,
        "restart_lock_path_for",
        lambda _process_identifier: tmp_path / "agent-session-restart-102.lock",
    )
    monkeypatch.setattr(
        relaunch,
        "wait_for_agent_session_exit",
        lambda _process_identifier: pytest.fail("must reject the lock before waiting"),
    )

    assert (
        relaunch.relaunch_after_exit(
            Namespace(
                process_identifier=102,
                multiplexer_name="herdr",
                pane_identifier="pane-123",
                resume_command='["codex", "resume", "session-123"]',
                restart_lock_path=str(unrelated_lock_path),
                restart_lock_owner_token="unrelated-token",
                restart_launcher_ready_file_descriptor=-1,
            )
        )
        == 1
    )
    assert unrelated_lock_path.exists()


def test_relaunch_refuses_an_owner_token_that_does_not_match_the_lock(
    monkeypatch, tmp_path
):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock,
        "restart_lock_path_for",
        lambda _process_identifier: lock_path,
    )
    acquired_restart_lock = restart_lock.acquire_restart_lock(102)
    assert acquired_restart_lock is not None
    monkeypatch.setattr(
        relaunch,
        "wait_for_agent_session_exit",
        lambda _process_identifier: pytest.fail(
            "must reject the owner token before waiting"
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
                    restart_lock_owner_token="wrong-owner-token",
                    restart_launcher_ready_file_descriptor=-1,
                )
            )
            == 1
        )
    finally:
        restart_lock.release_restart_lock(acquired_restart_lock)


def test_relaunch_releases_its_lock_when_the_target_pane_is_not_ready(
    monkeypatch, tmp_path
):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock,
        "restart_lock_path_for",
        lambda _process_identifier: lock_path,
    )
    acquired_restart_lock = restart_lock.acquire_restart_lock(102)
    assert acquired_restart_lock is not None
    monkeypatch.setattr(relaunch, "relaunch_target_is_ready", lambda *_arguments: False)

    assert (
        relaunch.relaunch_after_exit(
            Namespace(
                process_identifier=102,
                multiplexer_name="herdr",
                pane_identifier="pane-123",
                resume_command='["codex", "resume", "session-123"]',
                restart_lock_path=str(lock_path),
                restart_lock_owner_token=acquired_restart_lock.owner_token,
                restart_launcher_ready_file_descriptor=-1,
            )
        )
        == 1
    )
    assert not lock_path.exists()


def test_relaunch_does_not_send_a_command_after_lock_ownership_changes(
    monkeypatch, tmp_path
):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock,
        "restart_lock_path_for",
        lambda _process_identifier: lock_path,
    )
    acquired_restart_lock = restart_lock.acquire_restart_lock(102)
    assert acquired_restart_lock is not None
    ready_reader_file_descriptor, ready_writer_file_descriptor = os.pipe()
    monkeypatch.setattr(relaunch, "relaunch_target_is_ready", lambda *_arguments: True)
    monkeypatch.setattr(
        relaunch,
        "wait_for_agent_session_exit",
        lambda _process_identifier: lock_path.write_text("replacement-owner-token")
        or True,
    )
    monkeypatch.setattr(
        relaunch,
        "wait_for_relaunch_target_idle",
        lambda *_arguments: True,
    )
    monkeypatch.setattr(
        relaunch_transport.subprocess,
        "run",
        lambda *_arguments, **_keywords: pytest.fail(
            "must not relaunch after ownership changes"
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
        assert os.read(ready_reader_file_descriptor, 1) == b"1"
    finally:
        os.close(ready_reader_file_descriptor)
        os.close(ready_writer_file_descriptor)
