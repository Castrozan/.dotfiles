import asyncio
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import silver_channel
from silver_channel import HOLDER_UNIT, SilverChannel
from voice_connection import IdentityConnection
from provider_fixtures import make_clip_call

GUILD_ID = 7
LISTENER_ID = 42


def channel_named(name, guild_id=GUILD_ID):
    return SimpleNamespace(name=name, guild=SimpleNamespace(id=guild_id))


def answer(stdout="", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


class FakeCommands:
    def __init__(self, status):
        self.status = status
        self.started = []

    def __call__(self, arguments):
        if arguments[0] == "avatar-talk":
            assert arguments[1:] == ["status"]
            if isinstance(self.status, Exception):
                raise self.status
            return self.status
        self.started.append(arguments)
        return answer()


def closed():
    return answer(json.dumps({"open": False, "live": False}))


def moves_to(commands, channel):
    silver = SilverChannel(GUILD_ID, "silver", commands)
    asyncio.run(silver.listener_moved_to(channel))


def test_entering_the_silver_channel_with_no_conversation_starts_the_holder():
    commands = FakeCommands(closed())
    moves_to(commands, channel_named("silver"))
    assert commands.started == [
        ["systemctl", "--user", "start", "--no-block", HOLDER_UNIT]
    ]


@pytest.mark.parametrize("name", ["General", "Silver", "silver-2", ""])
def test_any_other_channel_starts_nothing(name):
    commands = FakeCommands(closed())
    moves_to(commands, channel_named(name))
    assert commands.started == []


def test_a_silver_named_channel_of_another_server_starts_nothing():
    commands = FakeCommands(closed())
    moves_to(commands, channel_named("silver", guild_id=GUILD_ID + 1))
    assert commands.started == []


def test_leaving_voice_starts_nothing():
    commands = FakeCommands(closed())
    moves_to(commands, None)
    assert commands.started == []


@pytest.mark.parametrize(
    "status",
    [
        answer(json.dumps({"open": True, "seat": "room"})),
        answer(json.dumps({"open": True, "seat": "discord"})),
        answer("not json"),
        answer("[]"),
        answer("{}"),
        answer("", returncode=1),
        None,
    ],
)
def test_an_open_or_unreadable_conversation_starts_nothing(status):
    commands = FakeCommands(status)
    moves_to(commands, channel_named("silver"))
    assert commands.started == []


def test_the_status_and_start_commands_are_bounded_by_a_timeout(monkeypatch):
    run = Mock(return_value=answer())
    monkeypatch.setattr(silver_channel.subprocess, "run", run)
    silver_channel.run_command(["avatar-talk", "status"])
    assert run.call_args.kwargs["timeout"] == silver_channel.COMMAND_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "failure", [subprocess.TimeoutExpired("avatar-talk", 1), FileNotFoundError()]
)
def test_a_command_that_cannot_run_is_no_answer(monkeypatch, failure):
    monkeypatch.setattr(silver_channel.subprocess, "run", Mock(side_effect=failure))
    assert silver_channel.run_command(["avatar-talk", "status"]) is None


def connection_with(silver):
    identity = SimpleNamespace(client=SimpleNamespace(user=SimpleNamespace(id=100)))
    call = SimpleNamespace(follow_listener=AsyncMock(), observe_bot_movement=Mock())
    return IdentityConnection(identity, call, LISTENER_ID, set(), silver), call


def voice_move(member_id, before, after):
    member = SimpleNamespace(id=member_id)
    return member, SimpleNamespace(channel=before), SimpleNamespace(channel=after)


def test_the_listener_entering_a_channel_is_reported_to_the_silver_channel():
    silver = SimpleNamespace(listener_moved_to=AsyncMock())
    connection, _call = connection_with(silver)
    after = channel_named("silver")
    asyncio.run(connection.on_voice_state_update(*voice_move(LISTENER_ID, None, after)))
    silver.listener_moved_to.assert_awaited_once_with(after)


def test_someone_else_moving_or_the_listener_staying_is_not_reported():
    silver = SimpleNamespace(listener_moved_to=AsyncMock())
    connection, _call = connection_with(silver)
    silver_room = channel_named("silver")
    asyncio.run(connection.on_voice_state_update(*voice_move(99, None, silver_room)))
    asyncio.run(
        connection.on_voice_state_update(
            *voice_move(LISTENER_ID, silver_room, silver_room)
        )
    )
    silver.listener_moved_to.assert_not_awaited()


def utterances_kept_in_channel(tmp_path, avatar_channel_name, channel_name):
    async def scenario():
        _module, call, _playback, connection = make_clip_call(
            tmp_path, avatar_channel_name=avatar_channel_name
        )
        connection.channel.name = channel_name
        await call.join()
        call._receiver.check_silence = lambda: [(LISTENER_ID, b"pcm")]
        kept = call._finished_utterances(0.0)
        await call.leave()
        return kept

    return asyncio.run(scenario())


def test_the_bridge_drops_the_listeners_utterances_in_the_silver_channel(tmp_path):
    assert utterances_kept_in_channel(tmp_path, "silver", "silver") == []


def test_the_bridge_keeps_the_listeners_utterances_in_every_other_channel(tmp_path):
    assert utterances_kept_in_channel(tmp_path, "silver", "call") == [b"pcm"]


def test_without_a_silver_channel_the_bridge_keeps_every_utterance(tmp_path):
    assert utterances_kept_in_channel(tmp_path, None, "silver") == [b"pcm"]
