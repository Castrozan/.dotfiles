from __future__ import annotations

from pathlib import Path

from capture_queue.captures import PROCESSED_MARKER
from evidence.open_groups import open_groups
from proposals.cards import CardsInvalid
from proposals.group_extension import extend_group
from proposals.new_groups import open_new_group
from proposals.proposal_context import ProposalContext
from pull_requests import GROUP_BRANCH_PREFIX


def capture_problems(groups: list[dict], inbox_directory: Path) -> list[str]:
    problems = []
    for card in (card for group in groups for card in group["cards"]):
        capture_path = inbox_directory / card["capture"]
        if not capture_path.is_file():
            problems.append(f"capture {card['capture']} is not in the inbox")
        elif PROCESSED_MARKER in capture_path.read_text(
            encoding="utf-8", errors="replace"
        ):
            problems.append(f"capture {card['capture']} is already done")
    return problems


def open_group_by_capture(context: ProposalContext) -> dict[str, int]:
    pull_requests = context.forge.open_pull_requests(GROUP_BRANCH_PREFIX)
    groups = open_groups(context.repository_directory, pull_requests)
    return {
        capture: group["number"] for group in groups for capture in group["captures"]
    }


def listed_elsewhere_problems(
    groups: list[dict], group_by_capture: dict[str, int]
) -> list[str]:
    return [
        f"capture {card['capture']} is already in open group #{group_by_capture[card['capture']]}; target it"
        for group in groups
        for card in group["cards"]
        if group_by_capture.get(card["capture"], group.get("target_pull_request"))
        != group.get("target_pull_request")
    ]


def require_unproposed_pending_captures(
    context: ProposalContext, groups: list[dict]
) -> None:
    problems = capture_problems(groups, context.inbox_directory)
    problems += listed_elsewhere_problems(groups, open_group_by_capture(context))
    if problems:
        raise CardsInvalid(problems)


def propose_groups(context: ProposalContext, groups: list[dict]) -> list[dict]:
    require_unproposed_pending_captures(context, groups)
    return [
        extend_group(context, group)
        if group.get("target_pull_request")
        else open_new_group(context, group)
        for group in groups
    ]
