from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument, current_timestamp
from ..record_store import all_records, load_record, save_record, state_directory
from ..user_model.directives import default_user_model_path, read_directives
from .events import (
    LEARNING_OUTCOMES,
    deviation_candidates,
    learned_card,
    learning_statistics,
    pending_learning_events,
    require_directive_cites_card,
)
from .repository_history import commits_touching_since


def add_parser(subcommands) -> None:
    learn = subcommands.add_parser(
        "learn",
        help="the loop that turns escalations, overrides and deviations into USER.md",
    )
    learn.add_argument("--dir", default=str(state_directory("orchestrator-decisions")))
    commands = learn.add_subparsers(dest="learn_command", required=True)

    pending_command = commands.add_parser(
        "pending", help="learning events still waiting for an outcome"
    )
    pending_command.set_defaults(handler=command_pending)

    scan_command = commands.add_parser(
        "scan",
        help="record later commits that touched work done under orchestrator decisions",
    )
    scan_command.set_defaults(handler=command_scan)

    resolve_command = commands.add_parser(
        "resolve", help="close a learning event with what USER.md now says"
    )
    resolve_command.add_argument("identifier")
    resolve_command.add_argument("--outcome", required=True, choices=LEARNING_OUTCOMES)
    resolve_command.add_argument(
        "--directive", help="the directive added or superseding"
    )
    resolve_command.add_argument(
        "--reason", required=True, help="the preference inferred, or why there is none"
    )
    resolve_command.add_argument(
        "--user-model", default=str(default_user_model_path()), help="USER.md path"
    )
    resolve_command.set_defaults(handler=command_resolve)

    stats_command = commands.add_parser(
        "stats", help="how often the model decides as you"
    )
    stats_command.set_defaults(handler=command_stats)


def command_pending(arguments: argparse.Namespace, decision_directory: Path) -> int:
    for kind, card in pending_learning_events(all_records(decision_directory)):
        print("\t".join([card["id"], kind, card["requester"], card["question"]]))
    return 0


def linked_commits(cards: list[dict]) -> set[str]:
    return {
        commit for card in cards for commit in card.get("work", {}).get("commits", [])
    }


def command_scan(arguments: argparse.Namespace, decision_directory: Path) -> int:
    cards = all_records(decision_directory)
    already_linked = linked_commits(cards)
    for card in cards:
        candidates = deviation_candidates(card, already_linked, commits_touching_since)
        recorded = {deviation["commit"] for deviation in card.get("deviations", [])}
        fresh = [commit for commit in candidates if commit not in recorded]
        if not fresh:
            continue
        detected_at = current_timestamp()
        deviations = card.get("deviations", []) + [
            {"commit": commit, "detected_at": detected_at} for commit in fresh
        ]
        save_record(decision_directory, card["id"], {**card, "deviations": deviations})
        print("\t".join([card["id"], *fresh]))
    return 0


def command_resolve(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = learned_card(
        load_record(decision_directory, arguments.identifier),
        arguments.outcome,
        arguments.directive,
        arguments.reason,
    )
    if arguments.directive:
        require_directive_cites_card(
            card["id"], arguments.directive, read_directives(Path(arguments.user_model))
        )
    save_record(decision_directory, card["id"], card)
    return 0


def command_stats(arguments: argparse.Namespace, decision_directory: Path) -> int:
    statistics = learning_statistics(all_records(decision_directory))
    print(json.dumps(statistics, indent=2))
    return 0


def command_learn(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.dir))
    except InvalidPeerDocument as failure:
        print(f"orchestrator learn: {failure}", file=sys.stderr)
        return 1
