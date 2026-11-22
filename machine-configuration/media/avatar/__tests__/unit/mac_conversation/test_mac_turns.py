import contextlib
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import conversation_state
import mac_turns
import pytest
import utterances
from conversation_addressee import Addressee
from conversation_state import ConversationPhase
from room_turns import (
    FINISHED,
    INTERRUPTED,
    outcome,
    owner_finishes,
    owner_speaking,
    said,
    withheld_because,
)

SPEECH = SimpleNamespace(text="Good evening", emotion="neutral", voice=None, wait=1)


@pytest.fixture
def mac_room(monkeypatch, tmp_path):
    stage = Mock()
    stage.standing = contextlib.nullcontext
    speaker = Mock(return_value=subprocess.CompletedProcess([], 0, FINISHED))
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.setattr(mac_turns, "mac_stage", stage)
    monkeypatch.setattr(mac_turns.voice_turns.subprocess, "run", speaker)
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    said(tmp_path, 1, "Good evening, are you there?")
    utterances.remember(tmp_path, 1)
    return SimpleNamespace(directory=tmp_path, speaker=speaker)


def reply(mac_room):
    with pytest.raises(SystemExit):
        mac_turns.reply(SPEECH, mac_room.directory)


def test_a_current_reply_plays_on_this_mac(mac_room, capsys):
    reply(mac_room)
    assert mac_room.speaker.call_args.args[0] == [
        "avatar-command",
        "speak",
        "Good evening",
        "neutral",
        "speakers",
    ]
    assert capsys.readouterr().out == FINISHED


def test_a_reply_the_owner_talks_over_is_withheld_on_this_mac(mac_room, capsys):
    owner_speaking(mac_room.directory)
    owner_finishes(mac_room.directory, 0.2, (2, "wait, one more thing"))
    reply(mac_room)
    assert not mac_room.speaker.called
    assert outcome(capsys.readouterr().out) == withheld_because("unheard")


def test_a_reply_behind_an_interrupted_one_is_withheld_on_this_mac(mac_room, capsys):
    mac_room.speaker.return_value = subprocess.CompletedProcess([], 0, INTERRUPTED)
    reply(mac_room)
    reply(mac_room)
    assert mac_room.speaker.call_count == 1
    assert outcome(capsys.readouterr().out) == withheld_because("queued")


def test_asking_on_this_mac_withholds_speech_but_hears_what_was_said(mac_room, capsys):
    said(mac_room.directory, 2, "Hello?")
    mac_turns.ask(SPEECH, mac_room.directory)
    assert not mac_room.speaker.called
    withheld, heard = capsys.readouterr().out.splitlines()
    assert json.loads(withheld) == withheld_because("unheard")
    assert heard == "[voice] Hello?"


def test_a_session_the_room_did_not_turn_to_may_not_reply(mac_room, monkeypatch):
    conversation_addressee.hand_to(
        mac_room.directory, Addressee("w1:p1", "Sasaki Kojirou", 0)
    )
    monkeypatch.setenv("HERDR_PANE_ID", "w9:p9")
    with pytest.raises(RuntimeError, match="holds the room"):
        mac_turns.reply(SPEECH, mac_room.directory)
    assert not mac_room.speaker.called
