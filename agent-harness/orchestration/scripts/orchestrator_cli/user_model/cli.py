from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from .directives import (
    DIRECTIVE_KINDS,
    Directive,
    append_directive,
    default_user_model_path,
    read_directives,
    supersede_directive,
)
from .publication import UserModelPublicationFailure, published_change


def add_directive_arguments(command) -> None:
    command.add_argument("--kind", required=True, choices=DIRECTIVE_KINDS)
    command.add_argument("--scope", required=True, help="where the directive applies")
    command.add_argument("--rule", required=True, help="the rest of the sentence")
    command.add_argument(
        "--source", required=True, help="card id, or the human's words with a date"
    )


def add_parser(subcommands) -> None:
    user = subcommands.add_parser(
        "user", help="the USER.md user model orchestrators decide by"
    )
    user.add_argument("--file", default=str(default_user_model_path()))
    commands = user.add_subparsers(dest="user_command", required=True)

    list_command = commands.add_parser("list", help="directives, active by default")
    list_command.add_argument("--all", action="store_true")
    list_command.set_defaults(handler=command_list)

    add_command = commands.add_parser("add", help="append a new active directive")
    add_directive_arguments(add_command)
    add_command.set_defaults(handler=command_add)

    supersede_command = commands.add_parser(
        "supersede", help="replace an active directive, keeping the old one as history"
    )
    supersede_command.add_argument("identifier")
    add_directive_arguments(supersede_command)
    supersede_command.set_defaults(handler=command_supersede)


def directive_fields(arguments: argparse.Namespace) -> dict:
    return {
        "kind": arguments.kind,
        "scope": arguments.scope,
        "rule": arguments.rule,
        "source": arguments.source,
    }


def command_list(arguments: argparse.Namespace, user_model: Path) -> int:
    for directive in read_directives(user_model):
        if arguments.all or directive.active:
            print(directive.line())
    return 0


def persisted_change(user_model: Path, change: Callable[[], Directive]) -> Directive:
    if user_model.expanduser().resolve() != default_user_model_path().resolve():
        return change()
    return published_change(user_model.expanduser().resolve(), change)


def command_add(arguments: argparse.Namespace, user_model: Path) -> int:
    def add() -> Directive:
        read_directives(user_model)
        return append_directive(user_model, directive_fields(arguments))

    print(persisted_change(user_model, add).identifier)
    return 0


def command_supersede(arguments: argparse.Namespace, user_model: Path) -> int:
    def supersede() -> Directive:
        return supersede_directive(
            user_model, arguments.identifier, directive_fields(arguments)
        )

    print(persisted_change(user_model, supersede).identifier)
    return 0


def command_user(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.file))
    except (InvalidPeerDocument, UserModelPublicationFailure) as failure:
        print(f"orchestrator user: {failure}", file=sys.stderr)
        return 1
