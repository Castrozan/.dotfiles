from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from application.apply import ApplyRefused, ApplyRequest, apply_pull_request
from application.card_actions import CardActionContext
from application.session_launch import HerdrSessionLauncher
from capture_queue.claims import default_claim_owner
from forge_adapter import ForgeAdapter, ForgeUnavailable
from gather import GatherSources, gather_document
from origins.transport import OriginTransport
from proposals.cards import (
    CardsInvalid,
    example_cards_document,
    validated_cards_document,
)
from proposals.decision_files import DecisionFileUnreadable
from proposals.git_worktrees import GitOperationFailed
from proposals.propose import ProposalContext, propose_groups

WORKFLOW_FAILURES = (
    ForgeUnavailable,
    GitOperationFailed,
    CardsInvalid,
    DecisionFileUnreadable,
    ApplyRefused,
)


def print_json(document) -> None:
    print(json.dumps(document, indent=2, ensure_ascii=False))


def reported_failure(error: Exception) -> int:
    print(f"{type(error).__name__}: {error}", file=sys.stderr)
    return 1


def command_gather(arguments: argparse.Namespace) -> int:
    sources = GatherSources(
        inbox_directory=arguments.inbox,
        vault_directory=arguments.vault,
        repository_directory=arguments.repository,
        forge=ForgeAdapter(arguments.repository),
        transport=OriginTransport(),
    )
    try:
        document = gather_document(sources, datetime.now().astimezone())
    except WORKFLOW_FAILURES as error:
        return reported_failure(error)
    arguments.output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"gathered {len(document['captures'])} captures and {len(document['open_groups'])} open groups into {arguments.output}"
    )
    return 0


def command_propose(arguments: argparse.Namespace) -> int:
    if arguments.example:
        print_json(example_cards_document())
        return 0
    context = ProposalContext(
        repository_directory=arguments.repository,
        inbox_directory=arguments.inbox,
        forge=ForgeAdapter(arguments.repository),
        now=datetime.now().astimezone(),
    )
    try:
        groups = validated_cards_document(
            json.loads(arguments.cards.read_text(encoding="utf-8"))
        )
        print_json(propose_groups(context, groups))
    except (*WORKFLOW_FAILURES, json.JSONDecodeError) as error:
        return reported_failure(error)
    return 0


def command_apply(arguments: argparse.Namespace) -> int:
    request = ApplyRequest(
        pull_request_number=arguments.pull_request,
        approval_comment_id=arguments.approval_comment,
        repository_directory=arguments.repository,
        forge=ForgeAdapter(arguments.repository),
        actions=CardActionContext(
            inbox_directory=arguments.inbox,
            vault_directory=arguments.vault,
            launcher=HerdrSessionLauncher(),
            claim_owner=default_claim_owner(),
            now=datetime.now(),
        ),
    )
    try:
        report = apply_pull_request(request)
    except WORKFLOW_FAILURES as error:
        return reported_failure(error)
    print_json(report)
    return 0 if report["merge"] in ("merged", "already-merged") else 2
