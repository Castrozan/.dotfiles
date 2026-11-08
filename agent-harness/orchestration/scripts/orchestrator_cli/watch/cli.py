from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ..record_store import state_directory
from .herdr_events import HerdrUnavailable
from .workspace_watch import WatchConfiguration, WorkspaceWatch

DEFAULT_TIMEOUT_MINUTES = 10.0


def positive_minutes(value: str) -> float:
    minutes = float(value)
    if not 0 < minutes < float("inf"):
        raise argparse.ArgumentTypeError("minutes must be a positive number")
    return minutes


def add_parser(subcommands) -> None:
    watch = subcommands.add_parser(
        "watch",
        help="stream one line per sub-session event in a herdr workspace; "
        "a session quiet past its timeout prints TIMEOUT until it answers",
    )
    watch.add_argument("--workspace", required=True, help="herdr workspace id")
    watch.add_argument(
        "--pane",
        action="append",
        dest="panes",
        default=[],
        help="follow only this session; repeat it when the workspace holds others",
    )
    watch.add_argument(
        "--timeout-minutes",
        type=positive_minutes,
        default=DEFAULT_TIMEOUT_MINUTES,
        help="how long each session may stay quiet before and between TIMEOUT lines",
    )
    watch.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )
    watch.add_argument(
        "--decisions-dir", default=str(state_directory("orchestrator-decisions"))
    )


def command_watch(arguments: argparse.Namespace) -> int:
    workspace_watch = WorkspaceWatch(
        WatchConfiguration(
            arguments.workspace,
            Path(arguments.reports_dir),
            Path(arguments.decisions_dir),
            arguments.timeout_minutes,
            frozenset(arguments.panes),
            os.environ.get("HERDR_PANE_ID"),
        )
    )
    try:
        workspace_watch.start()
        while True:
            for line in workspace_watch.next_lines():
                print(line, flush=True)
    except HerdrUnavailable as failure:
        print(f"orchestrator watch: {failure}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
