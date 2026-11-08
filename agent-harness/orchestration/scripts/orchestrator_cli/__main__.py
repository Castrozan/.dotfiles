from __future__ import annotations

import argparse
import sys

from .decisions import cli as decision_cli
from .handover import cli as handover_cli
from .learning import cli as learning_cli
from .reports import cli as report_cli
from .round import cli as round_cli
from .session_messages import cli as session_message_cli
from .user_model import cli as user_model_cli
from .watch import cli as watch_cli

COMMANDS = {
    "decision": (decision_cli.add_parser, decision_cli.command_decision),
    "report": (report_cli.add_parser, report_cli.command_report),
    "user": (user_model_cli.add_parser, user_model_cli.command_user),
    "learn": (learning_cli.add_parser, learning_cli.command_learn),
    "watch": (watch_cli.add_parser, watch_cli.command_watch),
    "round": (round_cli.add_parser, round_cli.command_round),
    "handover": (handover_cli.add_parser, handover_cli.command_handover),
    "dispatch": (
        session_message_cli.add_dispatch_parser,
        session_message_cli.command_session_message,
    ),
    "relay": (
        session_message_cli.add_relay_parser,
        session_message_cli.command_session_message,
    ),
}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Run sub-sessions as their orchestrator: decision cards, status "
        "reports, briefs and relays, the user model, the learning loop and the workspace "
        "watch.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for add_parser, _ in COMMANDS.values():
        add_parser(subcommands)
    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    _, command = COMMANDS[arguments.command]
    return command(arguments)


if __name__ == "__main__":
    sys.exit(main())
