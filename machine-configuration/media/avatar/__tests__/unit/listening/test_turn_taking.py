import argparse
import json
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import conversation_state
import pytest
import room_reach
import utterances
import voice_turns
from conversation_seat import Seat
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
from talk_runner import run_talk

CLOSED_PHASES = (
    ConversationPhase.CLOSED,
    ConversationPhase.INTERRUPTED,
    ConversationPhase.MEETING,
)


@pytest.fixture
def conversation(tmp_path, monkeypatch):
    monkeypatch.delenv(room_reach.ROOM_VARIABLE, raising=False)
    state = SimpleNamespace(
        directory=tmp_path,
        phase=ConversationPhase.OPEN,
        seat=Seat.DISCORD,
        speaker=Mock(return_value=subprocess.CompletedProcess([], 0, FINISHED)),
    )
    monkeypatch.setattr(conversation_state, "observe", lambda directory: state.phase)
    monkeypatch.setattr(conversation_seat, "current", lambda directory: state.seat)
    monkeypatch.setattr("voice_turns.subprocess.run", state.speaker)
    return state


def say(monkeypatch, conversation, text="Yes, I got it."):
    with pytest.raises(SystemExit) as exit_status:
        run_talk(monkeypatch, conversation.directory, "say", text)
    return exit_status.value.code


def spoken_texts(conversation):
    return [call.args[0][2] for call in conversation.speaker.call_args_list]


@pytest.mark.parametrize(
    ("seat", "output"), [(Seat.ROOM, "speakers"), (Seat.DISCORD, "discord")]
)
def test_a_current_reply_plays_at_once_on_every_seat(
    monkeypatch, conversation, capsys, seat, output
):
    conversation.seat = seat
    said(conversation.directory, 1, "Can you hear me?")
    utterances.remember(conversation.directory, 1)
    assert say(monkeypatch, conversation, "I can hear you.") == 0
    conversation.speaker.assert_called_once_with(
        ["avatar-command", "speak", "I can hear you.", "neutral", output],
        stdout=subprocess.PIPE,
        text=True,
        timeout=310,
    )
    assert capsys.readouterr().out == FINISHED


@pytest.mark.parametrize("phase", CLOSED_PHASES)
def test_speech_outside_an_open_conversation_is_never_held(
    monkeypatch, conversation, phase
):
    conversation.phase = phase
    said(conversation.directory, 1, "the meeting talks about the budget")
    owner_speaking(conversation.directory)
    assert say(monkeypatch, conversation, "Noted.") == 0
    assert spoken_texts(conversation) == ["Noted."]


@pytest.mark.parametrize("words_already_delivered", [False, True])
def test_a_reply_chained_behind_an_interrupted_one_is_withheld(
    monkeypatch, conversation, capsys, words_already_delivered
):
    directory = conversation.directory
    said(directory, 320, "Hey, did you get that? I did not hear a reply", False)
    utterances.remember(directory, 320)
    conversation.speaker.return_value = subprocess.CompletedProcess([], 0, INTERRUPTED)
    say(monkeypatch, conversation, "Slice is a script that lists paths.")
    if words_already_delivered:
        said(directory, 321, "Okay, but it's just a sequential graph, right?")
        utterances.remember(directory, 321)
    else:
        owner_speaking(directory)
    capsys.readouterr()
    assert say(monkeypatch, conversation, "Next steps: one, read that file.") == 0
    assert spoken_texts(conversation) == ["Slice is a script that lists paths."]
    assert outcome(capsys.readouterr().out) == withheld_because("queued")


@pytest.mark.parametrize(
    ("unheard", "being_said"),
    [
        ([(321, "Okay, but it's just a sequential graph, right?", False)], 322),
        ([], 321),
    ],
)
def test_a_reply_the_owner_talks_over_waits_for_him_and_is_withheld(
    monkeypatch, conversation, capsys, unheard, being_said
):
    directory = conversation.directory
    said(directory, 320, "Hey, did you get that? I did not hear a reply", False)
    utterances.remember(directory, 320)
    for entry in unheard:
        said(directory, *entry)
    owner_speaking(directory)
    owner_finishes(directory, 0.3, (being_said, "It's not an actual graph"))
    assert say(monkeypatch, conversation, "Yes, I got it.") == 0
    assert spoken_texts(conversation) == []
    assert outcome(capsys.readouterr().out) == withheld_because("unheard")


def test_a_sound_that_leaves_no_words_only_delays_the_reply(monkeypatch, conversation):
    said(conversation.directory, 1, "Can you hear me?")
    utterances.remember(conversation.directory, 1)
    owner_speaking(conversation.directory)
    owner_finishes(conversation.directory, 0.3)
    started = time.monotonic()
    assert say(monkeypatch, conversation, "I can hear you.") == 0
    assert 0.3 <= time.monotonic() - started < 1
    assert spoken_texts(conversation) == ["I can hear you."]


def test_ask_withholds_its_speech_but_still_hears_what_was_said(conversation, capsys):
    said(conversation.directory, 1, "Can you hear me?")
    utterances.remember(conversation.directory, 1)
    said(conversation.directory, 2, "Hello?")
    voice_turns.ask(
        argparse.Namespace(text="Yes.", emotion="neutral", voice=None, wait=1),
        conversation.directory,
    )
    assert spoken_texts(conversation) == []
    withheld, heard = capsys.readouterr().out.splitlines()
    assert json.loads(withheld) == withheld_because("unheard")
    assert heard == "[voice] Hello?"


def test_a_caller_without_a_follower_speaks_once_it_heard_everything(
    monkeypatch, conversation, capsys
):
    said(conversation.directory, 1, "What time is it?")
    voice_turns.hear(argparse.Namespace(wait=1), conversation.directory)
    assert say(monkeypatch, conversation, "Seven.") == 0
    said(conversation.directory, 2, "And the date?")
    capsys.readouterr()
    assert say(monkeypatch, conversation, "It is seven.") == 0
    assert spoken_texts(conversation) == ["Seven."]
    assert outcome(capsys.readouterr().out) == withheld_because("unheard")
