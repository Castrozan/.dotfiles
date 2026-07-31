from __future__ import annotations

import argparse
import json
import sys

from .peer_transport import (
    cancel_task_on_peer,
    peer_is_reachable,
    poll_task_until_terminal,
    read_task_from_peer,
    resolve_peer_endpoint,
    submit_task_to_peer,
)


def command_list(arguments: argparse.Namespace, peer_registry: dict) -> int:
    if not peer_registry:
        print(
            "no A2A peers declared; enable expose.a2a on a clawde agent",
            file=sys.stderr,
        )
        return 1
    reachability_by_peer_name = {
        name: peer_is_reachable(peer["endpoint"].rstrip("/"))
        for name, peer in sorted(peer_registry.items())
    }
    if arguments.json:
        print(
            json.dumps(
                {
                    name: {**peer_registry[name], "reachable": reachable}
                    for name, reachable in reachability_by_peer_name.items()
                },
                indent=2,
            )
        )
        return 0
    for name, reachable in reachability_by_peer_name.items():
        print(
            "\t".join(
                [
                    name,
                    peer_registry[name]["endpoint"],
                    "up" if reachable else "down",
                    peer_registry[name].get("description", ""),
                ]
            )
        )
    return 0


def command_send(arguments: argparse.Namespace, peer_registry: dict) -> int:
    endpoint = resolve_peer_endpoint(peer_registry, arguments.agent)
    print(submit_task_to_peer(endpoint, arguments.text)["id"])
    return 0


def command_ask(arguments: argparse.Namespace, peer_registry: dict) -> int:
    endpoint = resolve_peer_endpoint(peer_registry, arguments.agent)
    submitted_task = submit_task_to_peer(endpoint, arguments.text)
    finished_task = poll_task_until_terminal(
        endpoint, submitted_task["id"], arguments.timeout_seconds
    )
    print(finished_task.get("output", ""))
    return 0 if finished_task.get("state") == "completed" else 1


def command_status(arguments: argparse.Namespace, peer_registry: dict) -> int:
    endpoint = resolve_peer_endpoint(peer_registry, arguments.agent)
    print(json.dumps(read_task_from_peer(endpoint, arguments.task_id), indent=2))
    return 0


def command_cancel(arguments: argparse.Namespace, peer_registry: dict) -> int:
    endpoint = resolve_peer_endpoint(peer_registry, arguments.agent)
    print(cancel_task_on_peer(endpoint, arguments.task_id).get("state", "unknown"))
    return 0
