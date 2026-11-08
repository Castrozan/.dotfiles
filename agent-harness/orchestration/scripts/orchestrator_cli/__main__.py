from __future__ import annotations

import argparse
import sys

from .decisions import cli as decision_cli
from .learning import cli as learning_cli
from .reports import cli as report_cli
from .user_model import cli as user_model_cli
from .watch import cli as watch_cli

COMMANDS = {
    "decision": (decision_cli.add_parser, decision_cli.command_decision),
    "report": (report_cli.add_parser, report_cli.command_report),
    "user": (user_model_cli.add_parser, user_model_cli.command_user),
    "learn": (learning_cli.add_parser, learning_cli.command_learn),
    "watch": (watch_cli.add_parser, watch_cli.command_watch),
}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Run sub-sessions as their orchestrator: decision cards, status "
        "reports, the user model, the learning loop and the workspace watch.",
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
