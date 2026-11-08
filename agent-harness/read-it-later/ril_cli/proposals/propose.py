from __future__ import annotations

from pathlib import Path

from capture_queue.captures import PROCESSED_MARKER
from proposals.cards import CardsInvalid
from proposals.group_extension import extend_group
from proposals.new_groups import open_new_group
from proposals.proposal_context import ProposalContext


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


def require_pending_captures(groups: list[dict], inbox_directory: Path) -> None:
    problems = capture_problems(groups, inbox_directory)
    if problems:
        raise CardsInvalid(problems)


def propose_groups(context: ProposalContext, groups: list[dict]) -> list[dict]:
    require_pending_captures(groups, context.inbox_directory)
    return [
        extend_group(context, group)
        if group.get("target_pull_request")
        else open_new_group(context, group)
        for group in groups
    ]
