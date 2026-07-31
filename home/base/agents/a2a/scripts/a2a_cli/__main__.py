from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import (
    command_ask,
    command_cancel,
    command_list,
    command_send,
    command_status,
)
from .peer_transport import (
    DEFAULT_ANSWER_TIMEOUT_SECONDS,
    DEFAULT_PEER_REGISTRY_PATH,
    PeerRequestFailure,
    load_peer_registry,
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a2a",
        description="Talk to the fleet's A2A peers over HTTP, without loading an MCP.",
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_PEER_REGISTRY_PATH)
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_parser = subcommands.add_parser(
        "list", help="declared peers and whether each one answers"
    )
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)

    send_parser = subcommands.add_parser(
        "send", help="submit a task and print its id without waiting"
    )
    send_parser.add_argument("agent")
    send_parser.add_argument("text")
    send_parser.set_defaults(handler=command_send)

    ask_parser = subcommands.add_parser(
        "ask", help="submit a task and block until the peer answers"
    )
    ask_parser.add_argument("agent")
    ask_parser.add_argument("text")
    ask_parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_ANSWER_TIMEOUT_SECONDS
    )
    ask_parser.set_defaults(handler=command_ask)

    status_parser = subcommands.add_parser("status", help="read one task by id")
    status_parser.add_argument("agent")
    status_parser.add_argument("task_id")
    status_parser.set_defaults(handler=command_status)

    cancel_parser = subcommands.add_parser("cancel", help="interrupt one running task")
    cancel_parser.add_argument("agent")
    cancel_parser.add_argument("task_id")
    cancel_parser.set_defaults(handler=command_cancel)
    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    try:
        return arguments.handler(arguments, load_peer_registry(arguments.registry))
    except PeerRequestFailure as failure:
        print(f"a2a: {failure}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
