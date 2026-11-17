import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import discord_call
import pytest
import source_capture
from conversation_seat import Seat

JOIN_MESSAGE = "join a Discord voice channel first"


class FakeDiscordVoice:
    def __init__(self, joined_after_polls=0):
        self.calls = []
        self.status_polls = 0
        self.joined_after_polls = joined_after_polls

    def __call__(self, command, **keywords):
        assert keywords["timeout"] > 0
        self.calls.append(command[1:])
        stdout = ""
        if command[1] == "status":
            self.status_polls += 1
            stdout = json.dumps({"joined": self.status_polls > self.joined_after_polls})
        return SimpleNamespace(returncode=0, stdout=stdout)


@pytest.fixture
def no_waiting(monkeypatch):
    monkeypatch.setattr(discord_call.time, "sleep", lambda seconds: None)


def install(monkeypatch, fake):
    monkeypatch.setattr(discord_call.subprocess, "run", fake)
    return fake


def test_the_discord_seat_listens_to_the_discord_device_and_speaks_to_the_call():
    assert Seat.DISCORD == "discord"
    assert (
        conversation_seat.MICROPHONE_BY_SEAT[Seat.DISCORD]
        is source_capture.DISCORD_DEVICE
    )
    assert conversation_seat.SPEECH_OUTPUT_BY_SEAT[Seat.DISCORD] == "discord"
    assert Seat.DISCORD not in conversation_seat.MEETING_SEATS


def test_preparing_the_discord_seat_joins_following_the_listener_and_waits(
    monkeypatch, no_waiting
):
    fake = install(monkeypatch, FakeDiscordVoice(joined_after_polls=2))
    conversation_seat.prepare(Seat.DISCORD)
    assert fake.calls == [
        ["join", "--follow-listener"],
        ["status"],
        ["status"],
        ["status"],
    ]


def test_a_call_never_joined_tells_the_user_to_join_a_voice_channel(
    monkeypatch, no_waiting
):
    install(monkeypatch, FakeDiscordVoice(joined_after_polls=10**9))
    monkeypatch.setattr(discord_call, "JOIN_WAIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match=JOIN_MESSAGE):
        conversation_seat.prepare(Seat.DISCORD)


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError("discord-voice"), subprocess.TimeoutExpired("x", 1)],
)
def test_a_machine_without_a_working_bridge_fails_with_the_join_message(
    monkeypatch, no_waiting, failure
):
    install(monkeypatch, Mock(side_effect=failure))
    monkeypatch.setattr(discord_call, "JOIN_WAIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match=JOIN_MESSAGE):
        conversation_seat.prepare(Seat.DISCORD)


def test_a_status_that_is_not_json_is_not_a_call(monkeypatch):
    install(monkeypatch, Mock(return_value=SimpleNamespace(stdout="oops")))
    assert discord_call.in_call() is False


def test_other_seats_prepare_without_touching_the_bridge(monkeypatch):
    fake = install(monkeypatch, FakeDiscordVoice())
    conversation_seat.prepare(Seat.ROOM)
    assert fake.calls == []
