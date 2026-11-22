import argparse
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_effects
import conversation_seat
import conversation_state
import discord_call
import listen_cli
import listener_runtime
import listener_session
import live_opening
import pytest
import source_capture
import voice_turns
from conversation_seat import Seat
from conversation_state import ConversationPhase
from meetings import start
from remote_agent import AgentPane
from talk_runner import run_talk


def open_discord(tmp_path, monkeypatch):
    monkeypatch.setattr(listener_runtime, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(conversation_seat, "prepare", Mock())
    sources = Mock(side_effect=AssertionError("pulse sources were listed"))
    monkeypatch.setattr(listen_cli, "existing_sources", sources)
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None, seat="discord"), tmp_path
    )
    return begin, runner, sources


def test_opening_the_discord_seat_skips_the_pulse_check_and_announces_nothing(
    tmp_path, monkeypatch
):
    begin, runner, sources = open_discord(tmp_path, monkeypatch)
    readiness = start.bring_up.call_args.args[1][1]
    assert readiness() is True
    sources.assert_not_called()
    assert begin.call_args.args[2] == {"human": source_capture.DISCORD_DEVICE}
    assert begin.call_args.kwargs["seat"] is Seat.DISCORD
    assert not [call for call in runner.call_args_list if "speak" in call.args[0]]


def test_opening_the_room_seat_announces_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(listener_runtime, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(listener_session, "begin_listening", Mock())
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None, seat="room"), tmp_path
    )
    assert not [call for call in runner.call_args_list if "speak" in call.args[0]]


def test_a_listener_that_cannot_start_fails_the_open_and_leaves_the_call(
    tmp_path, monkeypatch
):
    leave = Mock()
    monkeypatch.setattr(discord_call, "leave", leave)
    monkeypatch.setattr(listener_runtime, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(conversation_seat, "prepare", Mock())
    monkeypatch.setattr(
        listener_session,
        "begin_listening",
        Mock(side_effect=subprocess.CalledProcessError(1, "avatar-listen")),
    )
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(subprocess.CalledProcessError):
        conversation_effects.open_conversation(
            argparse.Namespace(language="pt", character=None, seat="discord"), tmp_path
        )
    leave.assert_called_once_with()
    close.assert_called_once()


@pytest.mark.parametrize(
    ("seat", "calls"), [(Seat.DISCORD, [["leave"]]), (Seat.ROOM, [])]
)
def test_closing_leaves_the_call_only_for_a_discord_conversation(
    tmp_path, monkeypatch, seat, calls
):
    monkeypatch.setattr(conversation_seat, "current", lambda directory: seat)
    runner = Mock(return_value=SimpleNamespace(stdout=""))
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    monkeypatch.setattr(conversation_effects.user_units, "unit_active", lambda _: True)
    monkeypatch.setattr(conversation_effects, "hide_everywhere", Mock())
    conversation_effects.close_conversation(argparse.Namespace(), tmp_path)
    leaving = [
        call
        for call in runner.call_args_list
        if call.args[0][0] == discord_call.DISCORD_VOICE
    ]
    assert [call.args[0][1:] for call in leaving] == calls
    assert all(call.kwargs["check"] is False for call in leaving)
    assert all(call.kwargs["timeout"] > 0 for call in leaving)


def test_saying_while_the_seat_is_discord_speaks_into_the_call(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    monkeypatch.setattr(conversation_seat, "current", lambda directory: Seat.DISCORD)
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=""))
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "say", "Hello")
    assert runner.call_args.args[0] == [
        "avatar-command",
        "speak",
        "Hello",
        "neutral",
        "discord",
    ]


def test_the_live_voice_refuses_the_discord_seat_before_starting_anything(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(start, "bring_up", Mock())
    with pytest.raises(RuntimeError, match="no Discord seat"):
        live_opening.open_live_conversation(
            argparse.Namespace(agent=AgentPane(None, "pane"), seat="discord"),
            tmp_path,
        )
    start.bring_up.assert_not_called()
