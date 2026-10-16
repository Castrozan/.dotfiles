"""Opt-in CLI. Default status is a local cached read with no network calls."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

from .operations import dispatch, refresh, result
from .registry import Registry


def add_parser(subcommands):
    fleet = subcommands.add_parser(
        "fleet", help="quiet persistent host/session evidence and dispatch ledger"
    )
    fleet.add_argument(
        "--db",
        default=str(
            Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
            / "dot-fleet"
            / "registry.sqlite3"
        ),
    )
    commands = fleet.add_subparsers(dest="fleet_command", required=True)
    confirm = commands.add_parser(
        "confirm-host", help="register a host already confirmed by independent evidence"
    )
    confirm.add_argument("host")
    confirm.add_argument(
        "--transport", required=True, help="local or an existing SSH alias"
    )
    confirm.add_argument(
        "--evidence", required=True, help="reference to reviewed host confirmation"
    )
    status = commands.add_parser(
        "status", help="cached evidence; no network or inference"
    )
    status.add_argument(
        "--refresh",
        nargs="+",
        metavar="HOST",
        help="explicit bounded live metadata refresh, at most four hosts",
    )
    ingest = commands.add_parser(
        "ingest", help="import metadata collected by the fleet verification task"
    )
    ingest.add_argument("host")
    ingest.add_argument("file", type=Path)
    event = commands.add_parser(
        "event", help="invalidate metadata from an existing Herdr event consumer"
    )
    event.add_argument("host")
    event.add_argument("file", type=Path)
    event.add_argument("--evidence", required=True)
    assign = commands.add_parser(
        "assign", help="record an owner and task for an exact observed session"
    )
    send = commands.add_parser(
        "dispatch", help="explicitly submit one authorized task, with live preflight"
    )
    for parser in [assign, send]:
        parser.add_argument("host")
        parser.add_argument("pane")
        parser.add_argument("session")
        parser.add_argument("--owner", required=True)
        parser.add_argument(
            "--task", required=True, help="task reference, not raw transcript"
        )
    send.add_argument(
        "--request-id",
        required=True,
        help="durable unique intent ID; repeated IDs never resubmit",
    )
    send.add_argument(
        "--prompt",
        required=True,
        help="one line, at most 512 characters; refer to a brief accessible on target",
    )
    send.add_argument(
        "--execute",
        action="store_true",
        required=True,
        help="explicit authorization to submit this task",
    )
    poll = commands.add_parser(
        "result", help="read one remote task once; no polling loop"
    )
    poll.add_argument("request_id")
    verify = commands.add_parser(
        "verify", help="record independent verification of a reported result"
    )
    verify.add_argument("request_id")
    verify.add_argument("--evidence", required=True)
    reconcile = commands.add_parser(
        "reconcile",
        help="record independently checked evidence after a lost receipt/task record",
    )
    reconcile.add_argument("request_id")
    reconcile.add_argument("--evidence", required=True)
    choice = reconcile.add_mutually_exclusive_group(required=True)
    choice.add_argument("--remote-task-id")
    choice.add_argument("--outcome", choices=["completed", "failed", "not_submitted"])
    fleet.set_defaults(handler=command_fleet)


def command_fleet(arguments):
    registry = None
    try:
        registry = Registry(arguments.db)
        command = arguments.fleet_command
        answer = None
        if command == "confirm-host":
            registry.confirm_host(
                arguments.host, arguments.transport, arguments.evidence
            )
        elif command == "status":
            live = refresh(registry, arguments.refresh) if arguments.refresh else []
            answer = registry.status(live_hosts=live)
        elif command in {"ingest", "event"}:
            if arguments.file.stat().st_size > 2 * 1024 * 1024:
                raise ValueError("metadata import exceeds 2 MiB")
            document = json.loads(arguments.file.read_text())
            if command == "event":
                registry.event(arguments.host, document, arguments.evidence)
            else:
                registry.ingest(
                    arguments.host,
                    document["a2a"],
                    document["herdr"],
                    document["observed_at"],
                    document["evidence"],
                )
        elif command == "assign":
            registry.assign(
                arguments.host,
                arguments.pane,
                arguments.session,
                arguments.owner,
                arguments.task,
            )
        elif command == "dispatch":
            answer = dispatch(
                registry,
                arguments.request_id,
                arguments.host,
                arguments.pane,
                arguments.session,
                arguments.owner,
                arguments.task,
                arguments.prompt,
            )
        elif command == "result":
            answer = result(registry, arguments.request_id)
        elif command == "verify":
            answer = registry.verify(arguments.request_id, arguments.evidence)
        elif command == "reconcile":
            answer = registry.reconcile(
                arguments.request_id,
                arguments.evidence,
                arguments.remote_task_id,
                arguments.outcome,
            )
        if answer is not None:
            print(json.dumps(answer, indent=2))
        return 0
    except (
        ValueError,
        OSError,
        sqlite3.Error,
        KeyError,
        TypeError,
        AttributeError,
    ) as error:
        print(f"a2a fleet: {error}", file=sys.stderr)
        return 1
    finally:
        if registry is not None:
            registry.close()
