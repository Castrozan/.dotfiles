import json
import shlex
from types import SimpleNamespace
from unittest.mock import Mock

import agent_route
import live_bridge
import pytest
import remote_agent
import room_audio
from conversation_addressee import Addressee
from conversation_seat import MICROPHONE_BY_SEAT, Seat
from remote_agent import AgentPane

SESSIONS = {
    "avatar": {"paneId": "w4A:p1", "servant": "Sasaki Kojirou"},
    "nameless": {"paneId": "w4A:p2"},
}


def test_an_agent_on_another_machine_is_named_by_host_and_pane():
    assert remote_agent.parse("kira:w4A:p1") == AgentPane("kira", "w4A:p1")


@pytest.mark.parametrize("text", ["kira", "kira:", ":w4A:p1", "-oProxyCommand=x:p1"])
def test_a_malformed_agent_address_is_refused(text):
    with pytest.raises(ValueError, match="HOST:PANE"):
        remote_agent.parse(text)


def test_a_command_for_this_machine_runs_as_it_is():
    assert remote_agent.on_host(None, ["a2a", "list"]) == ["a2a", "list"]


@pytest.mark.parametrize(
    ("pane", "servant"),
    [("w4A:p1", "Sasaki Kojirou"), ("w4A:p2", None), ("w9Z:p9", None)],
)
def test_the_servant_is_read_from_the_sessions_of_the_agent_host(
    monkeypatch, pane, servant
):
    listing = Mock(return_value=SimpleNamespace(stdout=json.dumps(SESSIONS)))
    monkeypatch.setattr(remote_agent.subprocess, "run", listing)
    assert remote_agent.servant_at(AgentPane("kira", pane)) == servant
    command = listing.call_args.args[0]
    assert command[0] == "ssh"
    assert command[-2:] == ["kira", "a2a list --json"]
    assert listing.call_args.kwargs["timeout"] > 0


def test_a_task_for_an_agent_on_another_machine_crosses_as_one_quoted_command():
    holder = Addressee("w4A:p1", "Sasaki Kojirou", 0, "kira")
    command = agent_route.ask_command(holder, "is it clean; rm -rf ~?")
    assert command[0] == "ssh"
    assert command[-2] == "kira"
    crossed = shlex.split(command[-1])
    assert crossed[:2] == ["a2a", "ask"]
    assert crossed[-2] == "w4A:p1"
    assert "is it clean; rm -rf ~?" in crossed[-1]


def test_a_task_for_an_agent_on_this_machine_stays_local():
    command = agent_route.ask_command(Addressee("wW:pQZ", "Suzuka", 0), "anything")
    assert command[:2] == ["a2a", "ask"]


@pytest.mark.parametrize(
    ("seat", "sinks"),
    [
        (Seat.ROOM, [room_audio.DEFAULT_SINK, room_audio.LIP_SYNC_SINK]),
        (Seat.REMOTE, [room_audio.LIP_SYNC_SINK]),
    ],
)
def test_the_live_voice_plays_in_the_room_only_for_the_room_seat(
    monkeypatch, seat, sinks
):
    played = []

    def playback(rate, sink, client):
        played.append(sink)
        return Mock()

    monkeypatch.setattr(room_audio, "playback", playback)
    room_audio.Speaker(24000, live_bridge.VOICE_SINKS_BY_SEAT[seat])
    assert played == sinks
    assert MICROPHONE_BY_SEAT[Seat.REMOTE] != MICROPHONE_BY_SEAT[Seat.ROOM]
