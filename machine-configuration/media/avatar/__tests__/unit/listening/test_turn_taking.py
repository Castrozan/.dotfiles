import json
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import conversation_state
import listener
import pytest
import room_reach
import utterances
from conversation_seat import Seat
from conversation_state import ConversationPhase
from talk_runner import run_talk

FINISHED = '{"type":"speakAck","status":"finished","source":"elevenlabs"}\n'
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


def said(directory, sequence, text, turn_finished=True):
    entry = {
        "sequence": sequence,
        "time": time.time(),
        "source": "human",
        "text": text,
        "speaker": None,
        "turn_finished": turn_finished,
    }
    with (directory / "transcript.jsonl").open("a") as transcript:
        transcript.write(json.dumps(entry) + "\n")


def owner_speaking(directory):
    (directory / listener.SPEECH_IN_PROGRESS_MARKER).touch()


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
