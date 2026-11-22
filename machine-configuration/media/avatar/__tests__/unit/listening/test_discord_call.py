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
    def __init__(self, joined_after_polls=0, join_reply=None):
        self.calls = []
        self.status_polls = 0
        self.joined_after_polls = joined_after_polls
        self.join_reply = join_reply or {"joined": True}

    def __call__(self, command, **keywords):
        assert keywords["timeout"] > 0
        self.calls.append(command[1:])
        stdout = json.dumps(self.join_reply)
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


def test_preparing_the_discord_seat_joins_the_listener_channel_once_and_waits(
    monkeypatch, no_waiting
):
    fake = install(monkeypatch, FakeDiscordVoice(joined_after_polls=2))
    conversation_seat.prepare(Seat.DISCORD)
    assert fake.calls == [
        ["join"],
        ["status"],
        ["status"],
        ["status"],
    ]


def test_a_listener_outside_any_voice_channel_is_told_to_join_one(
    monkeypatch, no_waiting
):
    fake = install(
        monkeypatch,
        FakeDiscordVoice(join_reply={"error": "listener_not_in_allowed_voice_channel"}),
    )
    with pytest.raises(RuntimeError, match=JOIN_MESSAGE):
        conversation_seat.prepare(Seat.DISCORD)
    assert fake.calls == [["join"]]


@pytest.mark.parametrize(
    ("error", "message"),
    [
        *discord_call.JOIN_REFUSALS.items(),
        ("unforeseen_reason", "the Discord bridge refused with unforeseen_reason"),
    ],
)
def test_every_bridge_refusal_reaches_the_user_as_its_own_reason(
    monkeypatch, no_waiting, error, message
):
    install(monkeypatch, FakeDiscordVoice(join_reply={"error": error}))
    with pytest.raises(RuntimeError) as refusal:
        conversation_seat.prepare(Seat.DISCORD)
    assert str(refusal.value) == f"{discord_call.COULD_NOT_JOIN}: {message}"


def test_only_a_listener_outside_any_channel_is_told_to_join_one():
    listener_messages = [
        error
        for error, message in discord_call.JOIN_REFUSALS.items()
        if JOIN_MESSAGE in message
    ]
    assert listener_messages == ["listener_not_in_allowed_voice_channel"]


def test_a_join_that_never_shows_in_the_status_times_out_without_blaming_the_listener(
    monkeypatch, no_waiting
):
    install(monkeypatch, FakeDiscordVoice(joined_after_polls=10**9))
    monkeypatch.setattr(discord_call, "JOIN_WAIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match="did not join in time"):
        conversation_seat.prepare(Seat.DISCORD)


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError("discord-voice"), subprocess.TimeoutExpired("x", 1)],
)
def test_a_machine_without_a_working_bridge_says_the_bridge_did_not_answer(
    monkeypatch, no_waiting, failure
):
    install(monkeypatch, Mock(side_effect=failure))
    with pytest.raises(RuntimeError, match="the Discord bridge did not answer"):
        conversation_seat.prepare(Seat.DISCORD)


def test_the_join_is_bounded_by_its_own_wait(monkeypatch):
    runner = status_reader(monkeypatch, json.dumps({"joined": True}))
    discord_call.join()
    assert runner.call_args_list[0].args[0] == [discord_call.DISCORD_VOICE, "join"]
    assert (
        runner.call_args_list[0].kwargs["timeout"] == discord_call.JOIN_TIMEOUT_SECONDS
    )


def test_a_status_that_is_not_json_is_not_a_call(monkeypatch):
    install(monkeypatch, Mock(return_value=SimpleNamespace(stdout="oops")))
    assert discord_call.in_call() is False


def status_reader(monkeypatch, stdout):
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=stdout))
    install(monkeypatch, runner)
    return runner


@pytest.mark.parametrize(
    ("status", "left"),
    [
        ({"joined": True, "listener_present": True}, False),
        ({"joined": True, "listener_present": False}, True),
        ({"joined": True}, True),
        ({"joined": False, "listener_present": False}, True),
        ({"joined": False}, True),
    ],
)
def test_the_call_ends_when_the_listener_is_not_in_the_joined_channel(
    monkeypatch, status, left
):
    status_reader(monkeypatch, json.dumps(status))
    assert discord_call.listener_left_the_call() is left


@pytest.mark.parametrize(
    "stdout", ["", "oops", "[]", '{"error": "bridge_not_running"}']
)
def test_a_status_that_cannot_be_read_never_ends_the_call(monkeypatch, stdout):
    status_reader(monkeypatch, stdout)
    assert discord_call.listener_left_the_call() is False


@pytest.mark.parametrize(
    "failure", [FileNotFoundError("discord-voice"), subprocess.TimeoutExpired("x", 5)]
)
def test_a_bridge_that_cannot_answer_never_ends_the_call(monkeypatch, failure):
    install(monkeypatch, Mock(side_effect=failure))
    assert discord_call.listener_left_the_call() is False


def test_the_status_is_read_with_a_short_bounded_wait(monkeypatch):
    runner = status_reader(monkeypatch, json.dumps({"joined": True}))
    discord_call.listener_left_the_call()
    assert runner.call_args.args[0] == [discord_call.DISCORD_VOICE, "status"]
    assert 0 < runner.call_args.kwargs["timeout"] <= 5


def test_other_seats_prepare_without_touching_the_bridge(monkeypatch):
    fake = install(monkeypatch, FakeDiscordVoice())
    conversation_seat.prepare(Seat.ROOM)
    assert fake.calls == []
