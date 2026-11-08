from __future__ import annotations

import argparse
import sys

from .commands import (
    command_acknowledge,
    command_ask,
    command_cancel,
    command_inbox,
    command_list,
    command_notify,
    command_send,
    command_status,
    command_whoami,
)
from .fleet.cli import add_parser as add_fleet_parser
from .peer_identity import with_peer_identities
from .peer_transport import (
    DEFAULT_ANSWER_TIMEOUT_SECONDS,
    DEFAULT_DAEMON_ENDPOINT,
    PeerRequestFailure,
    read_agent_directory,
)


PEER_TARGET_HELP = "peer name, paneId, Servant name, or harness session id"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a2a",
        description="Talk to any agent session on this machine over HTTP, without loading an MCP.",
    )
    parser.add_argument("--daemon", default=DEFAULT_DAEMON_ENDPOINT)
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_parser = subcommands.add_parser(
        "list", help="every agent session the daemon is currently attached to"
    )
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)

    send_parser = subcommands.add_parser(
        "send", help="submit a task and print its id without waiting"
    )
    send_parser.add_argument("agent", help=PEER_TARGET_HELP)
    send_parser.add_argument("text")
    send_parser.add_argument(
        "--sender",
        help="current Servant or session name; supply it when calling over ssh",
    )
    send_parser.set_defaults(handler=command_send)

    ask_parser = subcommands.add_parser(
        "ask", help="submit a task and block until the agent answers"
    )
    ask_parser.add_argument("agent", help=PEER_TARGET_HELP)
    ask_parser.add_argument("text")
    ask_parser.add_argument(
        "--sender",
        help="current Servant or session name; supply it when calling over ssh",
    )
    ask_parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_ANSWER_TIMEOUT_SECONDS
    )
    ask_parser.set_defaults(handler=command_ask)

    status_parser = subcommands.add_parser("status", help="read one task by id")
    status_parser.add_argument("agent", help=PEER_TARGET_HELP)
    status_parser.add_argument("task_id")
    status_parser.set_defaults(handler=command_status)

    cancel_parser = subcommands.add_parser("cancel", help="interrupt one running task")
    cancel_parser.add_argument("agent", help=PEER_TARGET_HELP)
    cancel_parser.add_argument("task_id")
    cancel_parser.set_defaults(handler=command_cancel)

    notify_parser = subcommands.add_parser(
        "notify",
        help="queue peer messages for delivery when the agent is idle",
    )
    notify_parser.add_argument("agent", help=PEER_TARGET_HELP)
    notify_parser.add_argument("text")
    notify_parser.add_argument("--sender", required=True, help="sender name")
    notify_parser.set_defaults(handler=command_notify)

    inbox_parser = subcommands.add_parser(
        "inbox", help="read unread peer data without consuming or submitting it"
    )
    inbox_parser.add_argument("agent", help=PEER_TARGET_HELP)
    inbox_parser.set_defaults(handler=command_inbox)

    acknowledge_parser = subcommands.add_parser(
        "ack",
        help="explicitly acknowledge a notification; repeated acknowledgement is safe",
    )
    acknowledge_parser.add_argument("agent", help=PEER_TARGET_HELP)
    acknowledge_parser.add_argument("notification_id")
    acknowledge_parser.set_defaults(handler=command_acknowledge)

    whoami_parser = subcommands.add_parser(
        "whoami", help="print the sender name a2a signs this session's messages with"
    )
    whoami_parser.add_argument(
        "--sender", help="explicit Servant or session name to validate and print"
    )
    whoami_parser.set_defaults(handler=command_whoami)
    add_fleet_parser(subcommands)
    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    if arguments.command == "fleet":
        return arguments.handler(arguments)
    try:
        return arguments.handler(
            arguments, with_peer_identities(read_agent_directory(arguments.daemon))
        )
    except PeerRequestFailure as failure:
        print(f"a2a: {failure}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
