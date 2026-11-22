import itertools
import json
import os
import subprocess
import time
from unittest.mock import Mock

import pytest
import transcript_log
import turn_taking
import utterances
import voice_turns
from room_turns import owner_finishes, owner_speaking, said, withheld_because
from turn_taking import WithheldReason

STOPPED = ("none", "just now", "long ago")
ROOM = ("quiet", "a sound without words", "words", "still speaking")
COMMAND = ["avatar-command", "speak", "Pronto.", "neutral", "discord"]


def stopped(directory, when):
    if when == "none":
        return
    turn_taking.remember_stopped_reply(directory)
    if when == "long ago":
        past = time.time() - turn_taking.REACTION_SECONDS - 1
        os.utime(directory / turn_taking.STOPPED_REPLY_FILE, (past, past))


def room(directory, state):
    if state == "quiet":
        return None
    owner_speaking(directory)
    if state == "still speaking":
        return None
    words = (3, "e o build") if state == "words" else None
    return owner_finishes(directory, 0.05, words)


def expected_reason(when, state, unheard_before):
    if when == "just now":
        return WithheldReason.QUEUED
    if state == "still speaking":
        return WithheldReason.SPEAKING
    if state == "words" or unheard_before:
        return WithheldReason.UNHEARD
    return None


def test_every_state_of_the_room_and_the_last_reply_decides_as_the_rules_say(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(turn_taking, "QUIET_WAIT_SECONDS", 0.2)
    cases = itertools.product(STOPPED, ROOM, (False, True))
    for index, (when, state, unheard_before) in enumerate(cases):
        directory = tmp_path / str(index)
        directory.mkdir()
        said(directory, 1, "roda os testes")
        utterances.remember(directory, 1)
        if unheard_before:
            said(directory, 2, "e mais uma coisa")
        stopped(directory, when)
        timer = room(directory, state)
        reason = turn_taking.withheld_reason(directory)
        if timer:
            timer.join()
        assert reason == expected_reason(when, state, unheard_before), (
            when,
            state,
            unheard_before,
        )


@pytest.mark.parametrize(
    ("status", "holds_the_next"),
    [
        ("finished", False),
        ("failed", False),
        ("interrupted", True),
        ("cancelled", True),
    ],
)
def test_only_a_reply_the_room_stopped_holds_the_one_behind_it(
    tmp_path, monkeypatch, status, holds_the_next
):
    acknowledged = json.dumps({"type": "speakAck", "status": status}) + "\n"
    speaker = Mock(return_value=subprocess.CompletedProcess([], 0, acknowledged))
    monkeypatch.setattr(voice_turns.subprocess, "run", speaker)
    voice_turns.spoken_in_turn(COMMAND, tmp_path)
    behind = voice_turns.spoken_in_turn(COMMAND, tmp_path)
    assert speaker.call_count == (1 if holds_the_next else 2)
    held = json.loads(behind.stdout) == withheld_because("queued")
    assert held is holds_the_next


def test_a_reply_after_the_caller_could_react_is_no_longer_queued(tmp_path):
    turn_taking.remember_stopped_reply(tmp_path)
    assert turn_taking.withheld_reason(tmp_path) is WithheldReason.QUEUED
    stopped(tmp_path, "long ago")
    assert turn_taking.withheld_reason(tmp_path) is None


def test_a_current_reply_never_waits(tmp_path, monkeypatch):
    for sequence in range(1, 2001):
        said(tmp_path, sequence, "uma frase")
    utterances.remember(tmp_path, 2000)
    monkeypatch.setattr(time, "sleep", Mock(side_effect=AssertionError("waited")))
    assert turn_taking.withheld_reason(tmp_path) is None


def test_a_withheld_reply_is_logged_with_its_reason(tmp_path, monkeypatch):
    report = Mock()
    monkeypatch.setattr(transcript_log, "report_to_log", report)
    said(tmp_path, 1, "espera")
    voice_turns.spoken_in_turn(COMMAND, tmp_path)
    record = json.loads(report.call_args.args[0])
    assert (record["phase"], record["status"], record["reason"]) == (
        "speech",
        "withheld",
        "unheard",
    )


def test_the_record_of_a_stopped_reply_stays_private(tmp_path):
    turn_taking.remember_stopped_reply(tmp_path)
    mode = (tmp_path / turn_taking.STOPPED_REPLY_FILE).stat().st_mode
    assert mode & 0o777 == 0o600
