import json
import math
import os
from argparse import Namespace
from types import SimpleNamespace

import pytest

from agent_session import relaunch, relaunch_transport, restart_lock

PANE = "pane-123"
RESUME_TEXT = "codex resume session-123"
RESUME_COMMAND = ["codex", "resume", "session-123"]
SHELL_SCREEN = "lucas $ codex resume session-123"


class Clock:
    """Stand in for the transport's clock so a quiet window costs no real time."""

    def __init__(self, events):
        self.events = events
        self.reading = 0.0

    def monotonic(self):
        return self.reading

    def sleep(self, seconds):
        self.events.append(("sleep", seconds))
        self.reading += seconds


def next_report(reports):
    return reports.pop(0) if len(reports) > 1 else reports[0]


def herdr_double(events, pane_screens, pane_is_idle_reports):
    """Answer the herdr calls the relaunch handshake makes, recording every one."""

    def run(command, **_keywords):
        events.append(("run", command))
        if command[:3] == ["herdr", "pane", "read"]:
            return SimpleNamespace(returncode=0, stdout=next_report(pane_screens))
        if command[:3] == ["herdr", "pane", "process-info"]:
            shell_is_in_the_foreground = next_report(pane_is_idle_reports)
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "result": {
                            "process_info": {
                                "shell_pid": 101,
                                "foreground_process_group_id": (
                                    101 if shell_is_in_the_foreground else 102
                                ),
                                "foreground_processes": [{"pid": 102}],
                            }
                        }
                    }
                ),
            )
        return SimpleNamespace(returncode=0)

    return run


def record_herdr_calls(monkeypatch, **reports):
    events = []
    monkeypatch.setattr(
        relaunch_transport.subprocess, "run", herdr_double(events, **reports)
    )
    monkeypatch.setattr(relaunch_transport, "time", Clock(events))
    return events


def only_herdr_verbs(events):
    return [
        tuple(entry[1][1:3]) if entry[0] == "run" else entry
        for entry in events
        if entry[0] == "sleep" or entry[1][:1] == ["herdr"]
    ]


def herdr_run_verbs(events):
    return [verb for verb in only_herdr_verbs(events) if verb[0] != "sleep"]


def typed_texts(events):
    return [
        entry[1][4]
        for entry in events
        if entry[0] == "run" and entry[1][1:3] == ["agent", "send"]
    ]


def screens_read_before_the_prompt(events):
    typing_calls = [
        position
        for position, entry in enumerate(events)
        if entry[0] == "run" and entry[1][1:3] == ["agent", "send"]
    ]
    return [
        entry
        for entry in events[: typing_calls[-1]]
        if entry[0] == "run" and entry[1][1:3] == ["pane", "read"]
    ]


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


def test_resumes_a_session_and_hands_the_resumed_harness_the_prompt(monkeypatch):
    events = record_herdr_calls(
        monkeypatch,
        pane_screens=[SHELL_SCREEN, "drawn interface"],
        pane_is_idle_reports=[False],
    )
    settle = (
        "sleep",
        relaunch_transport.DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS,
    )

    assert relaunch_transport.resume_and_continue_session(PANE, RESUME_COMMAND)
    assert only_herdr_verbs(events)[:5] == [
        ("agent", "send"),
        settle,
        ("pane", "send-keys"),
        ("pane", "process-info"),
        ("pane", "read"),
    ]
    assert only_herdr_verbs(events)[-3:] == [
        ("agent", "send"),
        settle,
        ("pane", "send-keys"),
    ]
    assert typed_texts(events) == [
        RESUME_TEXT,
        relaunch_transport.RESTART_CONTINUATION_PROMPT,
    ]


def test_holds_the_prompt_while_the_resumed_harness_is_still_repainting(monkeypatch):
    repaints = ["banner", "banner and tips", "whole interface"]
    events = record_herdr_calls(
        monkeypatch,
        pane_screens=[SHELL_SCREEN, *repaints],
        pane_is_idle_reports=[False],
    )

    assert relaunch_transport.resume_and_continue_session(PANE, RESUME_COMMAND)
    quiet_polls = math.ceil(
        relaunch_transport.PANE_OUTPUT_QUIET_SECONDS
        / relaunch_transport.PANE_POLL_INTERVAL_SECONDS
    )
    assert (
        len(screens_read_before_the_prompt(events)) == 1 + len(repaints) + quiet_polls
    )


def test_does_not_read_a_silent_startup_as_a_drawn_interface(monkeypatch):
    """Nothing is painted between the resume command and the harness's first frame,
    and a quiet window measured from there would type into a harness that is not
    listening yet."""
    silent_startup_polls = 40
    events = record_herdr_calls(
        monkeypatch,
        pane_screens=[*[SHELL_SCREEN] * silent_startup_polls, "drawn interface"],
        pane_is_idle_reports=[False],
    )

    assert relaunch_transport.resume_and_continue_session(PANE, RESUME_COMMAND)
    assert len(screens_read_before_the_prompt(events)) > silent_startup_polls


def test_refuses_to_continue_a_session_the_resume_command_never_started(monkeypatch):
    events = record_herdr_calls(
        monkeypatch,
        pane_screens=[SHELL_SCREEN],
        pane_is_idle_reports=[True],
    )

    assert not relaunch_transport.resume_and_continue_session(PANE, RESUME_COMMAND)
    assert typed_texts(events) == [RESUME_TEXT]
    assert ("pane", "read") not in herdr_run_verbs(events)


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
