from __future__ import annotations

import argparse
import sys
from pathlib import Path

from captures import DEFAULT_CLAIM_EXPIRY_MINUTES, default_capture_inbox_directory
from claims import VERDICT_CHOICES
from commands import (
    command_claim,
    command_list,
    command_probe,
    command_record,
    command_release,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ril",
        description="Queue state for the ReadItLater capture routine.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--inbox",
        type=Path,
        default=default_capture_inbox_directory(),
        help="Capture directory. Defaults to the ReadItLater inbox inside the vault.",
    )
    common.add_argument(
        "--expiry-minutes",
        type=int,
        default=DEFAULT_CLAIM_EXPIRY_MINUTES,
        help="Age at which a working claim goes stale and becomes reclaimable.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", parents=[common], help="List captures that are not done, newest first."
    )
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument(
        "--claimable",
        action="store_true",
        help="Only captures free to claim, hiding the ones a live claim holds.",
    )
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)

    claim_parser = subparsers.add_parser(
        "claim",
        parents=[common],
        help="Take a capture, refusing one another run already holds.",
    )
    claim_parser.add_argument("capture")
    claim_parser.add_argument("--by", help="Claim owner. Defaults to the hostname.")
    claim_parser.add_argument(
        "--force", action="store_true", help="Take over a live claim."
    )
    claim_parser.set_defaults(handler=command_claim)

    release_parser = subparsers.add_parser(
        "release",
        parents=[common],
        help="Drop a claim, returning the capture unworked.",
    )
    release_parser.add_argument("capture")
    release_parser.set_defaults(handler=command_release)

    record_parser = subparsers.add_parser(
        "record", parents=[common], help="Close a capture with its verdict."
    )
    record_parser.add_argument("capture")
    record_parser.add_argument("--verdict", required=True, choices=VERDICT_CHOICES)
    record_parser.add_argument("--outcome", required=True)
    record_parser.add_argument("--entry", help="Second Brain entry this fed.")
    record_parser.set_defaults(handler=command_record)

    probe_parser = subparsers.add_parser(
        "probe",
        parents=[common],
        help="Print outstanding work as a change-gate fingerprint: one line per open "
        "ril pull request carrying an unanswered comment, then the newest capture "
        "that has neither a marker nor a pull request of its own. Exits non-zero "
        "without printing when pull requests cannot be listed, so a watcher holds "
        "still rather than reproposing captures it cannot see.",
    )
    probe_parser.add_argument(
        "--repository",
        type=Path,
        default=Path.home() / ".dotfiles",
        help="Checkout whose pull requests pace the queue.",
    )
    probe_parser.set_defaults(handler=command_probe)

    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
