import subprocess
from unittest.mock import Mock

import listener_runtime
import pytest
import utterances
import voice_holder_cli
from default_holder import DefaultHolder

SILVER = DefaultHolder("silver", "darkness-shibu")


@pytest.fixture
def avatar_talk(monkeypatch, tmp_path):
    runner = Mock()
    monkeypatch.setattr(voice_holder_cli.subprocess, "run", runner)
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    monkeypatch.setattr(voice_holder_cli.signal, "signal", Mock())
    monkeypatch.setattr(voice_holder_cli, "configured", lambda directory: SILVER)
    return runner


def test_the_holder_opens_the_discord_conversation_with_itself_as_default_holder(
    avatar_talk, monkeypatch
):
    holding = Mock(side_effect=utterances.ConversationClosed)
    monkeypatch.setattr(voice_holder_cli.FloorHolder, "hold", holding)
    monkeypatch.setattr(
        voice_holder_cli.sys,
        "argv",
        [
            "avatar-voice-holder",
            "--hermes-profile",
            "silver",
            "--character",
            "darkness-shibu",
        ],
    )
    assert voice_holder_cli.main() == 0
    command = avatar_talk.call_args.args[0]
    assert command == [
        "avatar-talk",
        "open",
        "--seat",
        "discord",
        "--holder",
        "silver",
        "--character",
        "darkness-shibu",
    ]
    assert avatar_talk.call_args.kwargs["timeout"] > 0
    holding.assert_called_once()


def test_a_conversation_opened_without_this_holder_is_left_alone(
    avatar_talk, monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(voice_holder_cli, "configured", lambda directory: None)
    holding = Mock()
    monkeypatch.setattr(voice_holder_cli.FloorHolder, "hold", holding)
    with pytest.raises(RuntimeError):
        voice_holder_cli.hold_the_conversation(SILVER, tmp_path)
    holding.assert_not_called()


def test_a_refused_opening_ends_the_holder_with_a_failure(
    avatar_talk, monkeypatch, capsys
):
    avatar_talk.side_effect = subprocess.CalledProcessError(1, "avatar-talk")
    monkeypatch.setattr(
        voice_holder_cli.sys,
        "argv",
        ["avatar-voice-holder", "--hermes-profile", "silver"],
    )
    assert voice_holder_cli.main() == 1


def test_stopping_the_holder_closes_the_conversation_it_holds(avatar_talk, monkeypatch):
    monkeypatch.setattr(
        voice_holder_cli.FloorHolder,
        "hold",
        Mock(side_effect=voice_holder_cli.HolderStopped),
    )
    monkeypatch.setattr(
        voice_holder_cli.sys,
        "argv",
        [
            "avatar-voice-holder",
            "--hermes-profile",
            "silver",
            "--character",
            "darkness-shibu",
        ],
    )
    assert voice_holder_cli.main() == 0
    assert avatar_talk.call_args.args[0] == ["avatar-talk", "close"]
    assert avatar_talk.call_args.kwargs["timeout"] > 0
