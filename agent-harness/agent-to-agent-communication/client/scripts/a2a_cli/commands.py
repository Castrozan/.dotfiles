from __future__ import annotations

import argparse
import json
import sys

from .peer_transport import (
    acknowledge_peer_notification,
    cancel_task_on_peer,
    notify_peer,
    poll_task_until_terminal,
    read_peer_inbox,
    read_task_from_peer,
    resolve_peer_endpoint,
    submit_task_to_peer,
)
from .sender_identity import signed_input_text


def command_list(arguments: argparse.Namespace, agent_directory: dict) -> int:
    if not agent_directory:
        print(
            "the a2a daemon is running but no pane is hosting an agent right now",
            file=sys.stderr,
        )
        return 1
    if arguments.json:
        print(json.dumps(agent_directory, indent=2))
        return 0
    for name, agent in sorted(agent_directory.items()):
        print(
            "\t".join(
                [
                    name,
                    agent.get("harness", ""),
                    agent.get("paneId", ""),
                    agent.get("description", ""),
                ]
            )
        )
    return 0


def command_send(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    input_text = signed_input_text(arguments.text, arguments.sender, agent_directory)
    print(submit_task_to_peer(endpoint, input_text)["id"])
    return 0


def command_notify(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    print(json.dumps(notify_peer(endpoint, arguments.sender, arguments.text), indent=2))
    return 0


def command_inbox(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    print(json.dumps(read_peer_inbox(endpoint), indent=2))
    return 0


def command_acknowledge(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    print(
        json.dumps(
            acknowledge_peer_notification(endpoint, arguments.notification_id), indent=2
        )
    )
    return 0


def command_ask(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    input_text = signed_input_text(arguments.text, arguments.sender, agent_directory)
    submitted_task = submit_task_to_peer(endpoint, input_text)
    finished_task = poll_task_until_terminal(
        endpoint, submitted_task["id"], arguments.timeout_seconds
    )
    print(finished_task.get("output", ""))
    return 0 if finished_task.get("state") == "completed" else 1


def command_status(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    print(json.dumps(read_task_from_peer(endpoint, arguments.task_id), indent=2))
    return 0


def command_cancel(arguments: argparse.Namespace, agent_directory: dict) -> int:
    endpoint = resolve_peer_endpoint(agent_directory, arguments.agent)
    print(cancel_task_on_peer(endpoint, arguments.task_id).get("state", "unknown"))
    return 0
