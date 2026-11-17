import argparse
import json
from unittest.mock import Mock

import conversation_addressee
import conversation_effects
import conversation_state
import discord_call
import listener_session
import pytest
import servant_character
import speaking_floor
from conversation_addressee import Addressee
from conversation_state import ConversationPhase
from meetings import start
from talk_runner import run_talk
from wake_phrase import LiveSession

SILVER = Addressee("hermes:silver", "Silver", 0)
SASAKI = LiveSession("Sasaki Kojirou", "wW:pSK")
OTHER_PANE = "wW:pOT"


@pytest.fixture(autouse=True)
def open_conversation_without_units(monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.delenv("AVATAR_ROOM", raising=False)


@pytest.fixture
def avatar_commands(monkeypatch):
    commands = Mock()
    monkeypatch.setattr(servant_character.subprocess, "run", commands)
    return commands


@pytest.fixture
def teardown(monkeypatch):
    closing = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", closing)
    return closing


def discord_conversation_held_by_silver(directory, floor_holder):
    (directory / "listener.json").write_text(
        json.dumps(
            {
                "purpose": "conversation",
                "sources": {"human": "discord"},
                "seat": "discord",
                "default_holder": {
                    "profile": "silver",
                    "character": "darkness-shibu",
                },
            }
        )
    )
    conversation_addressee.hand_to(directory, floor_holder)


def open_discord_conversation(monkeypatch, directory, **options):
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(discord_call, "join", Mock())
    monkeypatch.setattr(listener_session, "stop_listening", Mock())
    monkeypatch.setattr(listener_session, "start_unit", Mock())
    monkeypatch.setattr(conversation_effects.subprocess, "run", Mock())
    monkeypatch.setattr(conversation_effects.voice_turns, "speak_on_seat", Mock())
    arguments = argparse.Namespace(
        language=None, character="darkness-shibu", seat="discord", **options
    )
    conversation_effects.open_conversation(arguments, directory)


def test_opening_with_a_holder_records_it_as_the_default_holder(tmp_path, monkeypatch):
    open_discord_conversation(monkeypatch, tmp_path, holder="silver")
    assert listener_session.read_configuration(tmp_path)["default_holder"] == {
        "profile": "silver",
        "character": "darkness-shibu",
    }


def test_opening_without_a_holder_records_no_default_holder(tmp_path, monkeypatch):
    open_discord_conversation(monkeypatch, tmp_path, holder=None)
    assert "default_holder" not in listener_session.read_configuration(tmp_path)


def test_a_servant_closing_hands_the_floor_back_to_the_default_holder(
    tmp_path, monkeypatch, capsys, avatar_commands, teardown
):
    discord_conversation_held_by_silver(
        tmp_path, Addressee(SASAKI.pane, SASAKI.servant, 5)
    )
    monkeypatch.setenv("HERDR_PANE_ID", SASAKI.pane)
    run_talk(monkeypatch, tmp_path, "close")
    teardown.assert_not_called()
    assert conversation_addressee.current(tmp_path) == Addressee(
        "hermes:silver", "Silver", 5
    )
    avatar_commands.assert_called_once()
    assert avatar_commands.call_args.args[0] == [
        "avatar-command",
        "character",
        "darkness-shibu",
    ]
    assert json.loads(capsys.readouterr().out) == {
        "open": True,
        "floor_returned_to": "Silver",
    }


def test_a_conversation_without_a_default_holder_ends_when_a_servant_closes(
    tmp_path, monkeypatch, teardown
):
    (tmp_path / "listener.json").write_text(
        json.dumps({"purpose": "conversation", "seat": "discord"})
    )
    conversation_addressee.hand_to(tmp_path, Addressee(SASAKI.pane, SASAKI.servant, 0))
    monkeypatch.setenv("HERDR_PANE_ID", SASAKI.pane)
    run_talk(monkeypatch, tmp_path, "close")
    teardown.assert_called_once()


def test_the_default_holder_closing_ends_the_conversation(
    tmp_path, monkeypatch, teardown
):
    discord_conversation_held_by_silver(tmp_path, SILVER)
    monkeypatch.setenv("HERDR_PANE_ID", SILVER.pane)
    run_talk(monkeypatch, tmp_path, "close")
    teardown.assert_called_once()


@pytest.mark.parametrize("pane", [None, OTHER_PANE])
def test_a_close_from_someone_not_holding_the_floor_ends_the_conversation(
    tmp_path, monkeypatch, teardown, pane
):
    discord_conversation_held_by_silver(
        tmp_path, Addressee(SASAKI.pane, SASAKI.servant, 0)
    )
    if pane:
        monkeypatch.setenv("HERDR_PANE_ID", pane)
    run_talk(monkeypatch, tmp_path, "close")
    teardown.assert_called_once()


def test_a_servant_cannot_claim_the_floor_from_a_default_holder_outside_any_pane(
    tmp_path,
):
    conversation_addressee.hand_to(tmp_path, SILVER)
    boundaries = speaking_floor.FloorBoundaries(
        sessions=lambda: [SASAKI], listening=lambda: True
    )
    holder = speaking_floor.claim(tmp_path, SASAKI.pane, boundaries)
    assert holder == SILVER
    assert not speaking_floor.may_speak(holder, SASAKI.pane)
