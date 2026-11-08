from __future__ import annotations

from proposals.cards import CardsInvalid
from proposals.decision_files import parse_decision_file
from proposals.git_worktrees import fetch_reference, file_at_reference
from proposals.proposal_context import (
    ProposalContext,
    pull_request_body,
    stored_group,
    write_and_push,
)
from pull_requests import (
    decision_path_for_branch,
    is_group_branch,
    signed_by_the_watcher,
)


def merged_cards(
    existing_cards: list[dict], incoming_cards: list[dict], added_at: str
) -> tuple[list[dict], list[str], list[str]]:
    incoming_by_capture = {card["capture"]: card for card in incoming_cards}
    existing_captures = {card["capture"] for card in existing_cards}
    kept = [
        {**incoming_by_capture.get(card["capture"], card), "added_at": card["added_at"]}
        for card in existing_cards
    ]
    added = [
        {**card, "added_at": added_at}
        for card in incoming_cards
        if card["capture"] not in existing_captures
    ]
    revised = [
        card["capture"]
        for card in incoming_cards
        if card["capture"] in existing_captures
    ]
    return kept + added, [card["capture"] for card in added], revised


def extension_comment(added: list[str], revised: list[str]) -> str:
    lines = [f"- added: {capture}" for capture in added] + [
        f"- revised: {capture}" for capture in revised
    ]
    caution = (
        "An approval written before this comment does not cover the added captures."
    )
    return signed_by_the_watcher("\n".join(["Updated the group:", *lines, "", caution]))


def extend_group(context: ProposalContext, group: dict) -> dict:
    number = group["target_pull_request"]
    pull_request = context.forge.pull_request(number)
    branch = str(pull_request.get("headRefName", ""))
    if str(pull_request.get("state", "")).upper() not in (
        "OPEN",
        "OPENED",
    ) or not is_group_branch(branch):
        raise CardsInvalid([f"pull request {number} is not an open RIL group"])
    reference = fetch_reference(context.repository_directory, branch)
    existing = parse_decision_file(
        file_at_reference(
            context.repository_directory, reference, decision_path_for_branch(branch)
        )
    )
    cards, added, revised = merged_cards(
        existing["cards"], group["cards"], context.added_at
    )
    merged = {
        **stored_group(existing, cards),
        "bundle_goal": group["bundle_goal"],
        **({"session": group["session"]} if group.get("session") else {}),
    }
    write_and_push(
        context,
        branch,
        reference,
        merged,
        f"docs(ril): extend the {existing['topic_slug']} group",
    )
    context.forge.replace_body(number, pull_request_body(merged, branch))
    context.forge.comment(number, extension_comment(added, revised))
    return {
        "number": number,
        "url": pull_request.get("url", ""),
        "branch": branch,
        "added": added,
        "revised": revised,
    }
