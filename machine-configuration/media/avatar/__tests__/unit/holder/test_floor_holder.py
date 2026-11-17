import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import conversation_state
import default_holder
import listener_runtime
import pytest
import servant_character
import transcript_log
import utterances
import voice_holder
import voice_turns
from conversation_addressee import Addressee
from conversation_seat import Seat
from conversation_state import ConversationPhase
from default_holder import DefaultHolder
from hermes_turn import FAILED_TURN_APOLOGY, HermesTurnError
from voice_holder import FloorHolder

SILVER = DefaultHolder("silver", "darkness-shibu")
SASAKI = Addressee("wW:pSK", "Sasaki Kojirou", 0)
WAIT_SECONDS = 5


def eventually(condition):
    deadline = time.monotonic() + WAIT_SECONDS
    while not condition():
        assert time.monotonic() < deadline, "the condition never came true"
        time.sleep(0.01)


class Room:
    def __init__(self, directory):
        self.directory = directory
        self.is_open = True
        self.heard = []
        self.spoken = []
        self.replies = []
        self.failure = None

    def say(self, text):
        transcript_log.append(self.directory / "transcript.jsonl", "human", text)

    def reply_to(self, heard):
        self.heard.append(heard)
        if self.failure:
            raise self.failure
        return self.replies.pop(0)

    def speak_on_seat(self, directory, text, seat):
        self.spoken.append((text, seat))
        if not self.replies:
            self.is_open = False

    def holder(self):
        return FloorHolder(self.directory, SILVER, self.reply_to, self.speak_on_seat)

    def hold_in_background(self):
        outcome = SimpleNamespace(error=None)

        def hold():
            try:
                self.holder().hold()
            except utterances.ConversationClosed as error:
                outcome.error = error

        thread = threading.Thread(target=hold, daemon=True)
        thread.start()
        return thread, outcome


@pytest.fixture
def room(monkeypatch, tmp_path):
    room = Room(tmp_path)
    (tmp_path / "listener.json").write_text(
        json.dumps({"purpose": "conversation", "seat": "discord"})
    )
    monkeypatch.setattr(
        conversation_state,
        "observe",
        lambda directory: (
            ConversationPhase.OPEN if room.is_open else ConversationPhase.CLOSED
        ),
    )
    monkeypatch.setattr(listener_runtime, "listening", lambda: True)
    monkeypatch.setattr(utterances, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(utterances, "POLL_SECONDS", 0.01)
    monkeypatch.setattr(voice_holder, "FLOOR_POLL_SECONDS", 0.01)
    monkeypatch.setattr(voice_turns, "FOLLOW_SLICE_SECONDS", 0.05)
    monkeypatch.setattr(servant_character, "subprocess", Mock())
    return room


def hold_until_closed(room):
    with pytest.raises(utterances.ConversationClosed):
        room.holder().hold()


def test_the_holder_gives_itself_the_floor_and_shows_its_character(room, tmp_path):
    room.is_open = False
    hold_until_closed(room)
    assert conversation_addressee.current(tmp_path) == Addressee(
        "hermes:silver", "Silver", 0
    )
    servant_character.subprocess.run.assert_called_once()
    assert servant_character.subprocess.run.call_args.args[0] == [
        "avatar-command",
        "character",
        "darkness-shibu",
    ]


def test_a_heard_turn_is_answered_through_the_seat_in_the_holders_voice(room):
    room.replies = ["Bom dia, Lucas."]
    room.say("bom dia")
    hold_until_closed(room)
    assert room.heard == ["bom dia"]
    assert room.spoken == [("Bom dia, Lucas.", Seat.DISCORD)]


def test_silence_is_not_spoken(room):
    room.replies = ["SILENCIO", "Aqui."]
    room.say("ruído")
    thread, _ = room.hold_in_background()
    eventually(lambda: room.heard == ["ruído"])
    time.sleep(0.2)
    assert room.spoken == []
    room.say("Silver, você está aí?")
    thread.join(WAIT_SECONDS)
    assert room.spoken == [("Aqui.", Seat.DISCORD)]


def test_a_turn_hermes_cannot_answer_is_apologised_for(room):
    room.failure = HermesTurnError("The Hermes turn exited 3")
    room.say("olá")
    room.replies = []
    hold_until_closed(room)
    assert room.spoken == [(FAILED_TURN_APOLOGY, Seat.DISCORD)]


def test_a_reply_ready_after_the_floor_moved_is_not_spoken(room, tmp_path):
    def hermes_while_the_room_turns(heard):
        conversation_addressee.hand_to(tmp_path, SASAKI)
        return "Tarde demais."

    room.say("olá")
    room.is_open = False
    holder = FloorHolder(
        tmp_path, SILVER, hermes_while_the_room_turns, room.speak_on_seat
    )
    holder.answer(heard="olá")
    assert room.spoken == []


def test_the_holder_waits_while_a_servant_holds_the_floor_and_resumes(room, tmp_path):
    room.replies = ["Voltei."]
    thread, _ = room.hold_in_background()
    eventually(lambda: conversation_addressee.current(tmp_path) is not None)
    conversation_addressee.hand_to(tmp_path, SASAKI)
    room.say("fala com o Sasaki")
    eventually(lambda: _lock_is_free(tmp_path))
    utterances.remember(tmp_path, 1)
    time.sleep(0.3)
    assert room.heard == []
    room.say("de volta para a Silver")
    default_holder.take_the_floor(tmp_path, SILVER)
    thread.join(WAIT_SECONDS)
    assert room.heard == ["de volta para a Silver"]
    assert room.spoken == [("Voltei.", Seat.DISCORD)]


def _lock_is_free(directory):
    try:
        with utterances.exclusive_consumer(directory):
            return True
    except utterances.ConversationBusy:
        return False


def test_the_holder_exits_when_the_conversation_closes_while_it_waits(room, tmp_path):
    thread, outcome = room.hold_in_background()
    eventually(lambda: conversation_addressee.current(tmp_path) is not None)
    conversation_addressee.hand_to(tmp_path, SASAKI)
    room.is_open = False
    thread.join(WAIT_SECONDS)
    assert isinstance(outcome.error, utterances.ConversationClosed)
