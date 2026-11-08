from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..record_store import state_directory
from .herdr_events import HerdrUnavailable
from .workspace_watch import WorkspaceWatch

DEFAULT_SAFETY_MINUTES = 30.0


def add_parser(subcommands) -> None:
    watch = subcommands.add_parser(
        "watch",
        help="stream one line per sub-session event in a herdr workspace; "
        "a quiet stretch prints stale reports as a safety net",
    )
    watch.add_argument("--workspace", required=True, help="herdr workspace id")
    watch.add_argument("--safety-minutes", type=float, default=DEFAULT_SAFETY_MINUTES)
    watch.add_argument("--reports-dir", default=str(state_directory("a2a-reports")))


def command_watch(arguments: argparse.Namespace) -> int:
    workspace_watch = WorkspaceWatch(
        arguments.workspace, Path(arguments.reports_dir), arguments.safety_minutes
    )
    try:
        workspace_watch.start()
        while True:
            for line in workspace_watch.next_lines():
                print(line, flush=True)
    except HerdrUnavailable as failure:
        print(f"a2a watch: {failure}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
