import json
from unittest.mock import Mock

import conversation_effects
import conversation_state
import listener_runtime
import pytest
from conversation_seat import Seat
from conversation_state import (
    ConversationAction,
    ConversationCommand,
    ConversationPhase,
)
from talk_runner import run_talk

OPEN_PHASES = (ConversationPhase.OPEN, ConversationPhase.LIVE)


@pytest.mark.parametrize("phase", OPEN_PHASES)
@pytest.mark.parametrize(
    ("open_seat", "requested_seat"),
    [(Seat.DISCORD, Seat.ROOM), (Seat.ROOM, Seat.DISCORD), (Seat.REMOTE, Seat.ROOM)],
)
def test_opening_another_seat_is_refused_while_a_conversation_is_open(
    phase, open_seat, requested_seat
):
    decision = conversation_state.decide(
        phase, ConversationCommand.OPEN, requested_seat, open_seat
    )
    assert decision is ConversationAction.REFUSE_SEAT_CHANGE


@pytest.mark.parametrize("phase", OPEN_PHASES)
@pytest.mark.parametrize("seat", list(Seat))
def test_opening_the_same_seat_or_no_seat_keeps_the_conversation_open(phase, seat):
    for requested_seat in (seat, None):
        decision = conversation_state.decide(
            phase, ConversationCommand.OPEN, requested_seat, seat
        )
        assert decision is ConversationAction.KEEP_OPEN


@pytest.mark.parametrize("phase", list(ConversationPhase))
@pytest.mark.parametrize("command", list(ConversationCommand))
def test_a_requested_seat_changes_only_the_decisions_that_keep_open(phase, command):
    pinned = conversation_state.TRANSITIONS[phase][command]
    decision = conversation_state.decide(phase, command, Seat.DISCORD, Seat.ROOM)
    if pinned is ConversationAction.KEEP_OPEN:
        assert decision is ConversationAction.REFUSE_SEAT_CHANGE
    else:
        assert decision is pinned


def with_open_conversation(monkeypatch, tmp_path, open_seat):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    monkeypatch.setattr(listener_runtime, "listening", lambda: True)
    (tmp_path / "listener.json").write_text(
        json.dumps({"purpose": "conversation", "seat": open_seat})
    )
    monkeypatch.setattr(conversation_effects, "open_conversation", Mock())
    monkeypatch.setattr(conversation_effects, "status", Mock())


def test_the_command_line_names_the_open_seat_when_it_refuses(
    monkeypatch, tmp_path, capsys
):
    with_open_conversation(monkeypatch, tmp_path, "discord")
    with pytest.raises(SystemExit) as finished:
        run_talk(monkeypatch, tmp_path, "open", "--seat", "room")
    assert finished.value.code == 1
    assert "A discord conversation is open" in capsys.readouterr().err
    conversation_effects.open_conversation.assert_not_called()


@pytest.mark.parametrize("arguments", [["open"], ["open", "--seat", "discord"]])
def test_the_command_line_keeps_the_same_seat_open(monkeypatch, tmp_path, arguments):
    with_open_conversation(monkeypatch, tmp_path, "discord")
    run_talk(monkeypatch, tmp_path, *arguments)
    conversation_effects.status.assert_called_once()
    conversation_effects.open_conversation.assert_not_called()


def test_a_meeting_still_refuses_an_open_of_the_discord_seat(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.MEETING
    )
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "open", "--seat", "discord")
    assert "A meeting is being transcribed" in capsys.readouterr().err
