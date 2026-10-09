import argparse

import pytest
from a2a_cli import commands, peer_transport
from a2a_cli.__main__ import build_argument_parser

PEER_DIRECTORY = {"peer": {"endpoint": "http://127.0.0.1:7000/agents/peer"}}


@pytest.mark.parametrize("command", [commands.command_send, commands.command_ask])
def test_task_commands_transmit_the_sender_with_the_input(command, monkeypatch):
    requests = []

    def request(method, url, payload=None):
        requests.append((method, url, payload))
        if method == "POST":
            return 201, {"id": "task-1", "state": "working"}
        return 200, {"id": "task-1", "state": "completed", "output": "done"}

    monkeypatch.setattr(peer_transport, "request_peer_json", request)
    arguments = argparse.Namespace(
        agent="peer",
        text="inspect the result",
        sender="Sasaki Kojirou",
        timeout_seconds=1,
    )

    assert command(arguments, PEER_DIRECTORY) == 0
    assert requests[0] == (
        "POST",
        "http://127.0.0.1:7000/agents/peer/tasks/send",
        {"input": "inspect the result — Sasaki Kojirou"},
    )


@pytest.mark.parametrize("command_name", ["send", "ask"])
def test_remote_calls_accept_an_explicit_sender(command_name):
    arguments = build_argument_parser().parse_args(
        [command_name, "peer", "inspect the result", "--sender", "Sasaki Kojirou"]
    )

    assert arguments.sender == "Sasaki Kojirou"


def test_the_same_signature_is_not_appended_twice(monkeypatch):
    requests = []

    def request(method, url, payload=None):
        requests.append(payload)
        return 201, {"id": "task-1"}

    monkeypatch.setattr(peer_transport, "request_peer_json", request)
    arguments = argparse.Namespace(
        agent="peer",
        text="inspect the result — Sasaki Kojirou",
        sender="Sasaki Kojirou",
    )

    commands.command_send(arguments, PEER_DIRECTORY)

    assert requests == [{"input": arguments.text}]
