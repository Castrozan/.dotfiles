from __future__ import annotations

import argparse
import sys
from pathlib import Path

from capture_queue.captures import (
    DEFAULT_CLAIM_EXPIRY_MINUTES,
    default_capture_inbox_directory,
)
from capture_queue.claims import VERDICT_CHOICES
from commands import (
    command_claim,
    command_list,
    command_probe,
    command_record,
    command_release,
)
from second_brain.index import default_vault_directory
from workflow_commands import command_apply, command_gather, command_propose


def shared_options() -> tuple[
    argparse.ArgumentParser, argparse.ArgumentParser, argparse.ArgumentParser
]:
    queue_options = argparse.ArgumentParser(add_help=False)
    queue_options.add_argument(
        "--inbox",
        type=Path,
        default=default_capture_inbox_directory(),
        help="Capture directory inside the vault.",
    )
    queue_options.add_argument(
        "--expiry-minutes",
        type=int,
        default=DEFAULT_CLAIM_EXPIRY_MINUTES,
        help="Age at which a working claim goes stale and becomes reclaimable.",
    )
    repository_options = argparse.ArgumentParser(add_help=False)
    repository_options.add_argument(
        "--repository",
        type=Path,
        default=Path.home() / ".dotfiles",
        help="Checkout whose pull requests hold the groups.",
    )
    vault_options = argparse.ArgumentParser(add_help=False)
    vault_options.add_argument(
        "--vault",
        type=Path,
        default=default_vault_directory(),
        help="Obsidian vault root.",
    )
    return queue_options, repository_options, vault_options


def add_queue_commands(subparsers, queue_options: argparse.ArgumentParser) -> None:
    list_parser = subparsers.add_parser(
        "list", parents=[queue_options], help="Captures not done, newest first."
    )
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument(
        "--claimable", action="store_true", help="Hide captures a live claim holds."
    )
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)
    claim_parser = subparsers.add_parser(
        "claim",
        parents=[queue_options],
        help="Take a capture another run does not hold.",
    )
    claim_parser.add_argument("capture")
    claim_parser.add_argument("--by", help="Claim owner. Defaults to the hostname.")
    claim_parser.add_argument(
        "--force", action="store_true", help="Take over a live claim."
    )
    claim_parser.set_defaults(handler=command_claim)
    release_parser = subparsers.add_parser(
        "release", parents=[queue_options], help="Return a claimed capture unworked."
    )
    release_parser.add_argument("capture")
    release_parser.set_defaults(handler=command_release)
    record_parser = subparsers.add_parser(
        "record", parents=[queue_options], help="Close a capture with its action."
    )
    record_parser.add_argument("capture")
    record_parser.add_argument("--verdict", required=True, choices=VERDICT_CHOICES)
    record_parser.add_argument("--outcome", required=True)
    record_parser.add_argument("--entry", help="Second Brain entry this fed.")
    record_parser.set_defaults(handler=command_record)


def add_group_commands(
    subparsers, queue_options, repository_options, vault_options
) -> None:
    probe_parser = subparsers.add_parser(
        "probe",
        parents=[queue_options, repository_options],
        help="Change-gate fingerprint: one line per open group pull request with an unanswered comment, then the "
        "newest pending capture no open group lists. Exits non-zero when groups cannot be read.",
    )
    probe_parser.set_defaults(handler=command_probe)
    gather_parser = subparsers.add_parser(
        "gather",
        parents=[queue_options, repository_options, vault_options],
        help="Read every pending capture no open group lists, its origin and its coverage evidence into one file.",
    )
    gather_parser.add_argument("--output", type=Path, required=True)
    gather_parser.set_defaults(handler=command_gather)
    propose_parser = subparsers.add_parser(
        "propose",
        parents=[queue_options, repository_options],
        help="Open or extend group pull requests from cards.",
    )
    propose_input = propose_parser.add_mutually_exclusive_group(required=True)
    propose_input.add_argument(
        "--cards", type=Path, help="Cards JSON written by triage."
    )
    propose_input.add_argument(
        "--example", action="store_true", help="Print a valid cards document."
    )
    propose_parser.set_defaults(handler=command_propose)
    apply_parser = subparsers.add_parser(
        "apply",
        parents=[queue_options, repository_options, vault_options],
        help="Execute an approved group pull request card by card, then merge it.",
    )
    apply_parser.add_argument("--pull-request", type=int, required=True)
    apply_parser.add_argument(
        "--approval-comment", required=True, help="Id of Lucas's approving comment."
    )
    apply_parser.set_defaults(handler=command_apply)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ril", description="ReadItLater inbox triage into grouped pull requests."
    )
    queue_options, repository_options, vault_options = shared_options()
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_queue_commands(subparsers, queue_options)
    add_group_commands(subparsers, queue_options, repository_options, vault_options)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
