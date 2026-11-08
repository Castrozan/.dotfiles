from __future__ import annotations

from proposals.cards import CardsInvalid
from proposals.git_worktrees import fetch_reference, git
from proposals.proposal_context import (
    PULL_REQUEST_TITLE_PREFIX,
    ProposalContext,
    pull_request_body,
    stored_group,
    write_and_push,
)
from pull_requests import group_branch_name


def open_new_group(context: ProposalContext, group: dict) -> dict:
    branch = group_branch_name(context.proposal_date, group["topic_slug"])
    if git(context.repository_directory, "ls-remote", "--heads", "origin", branch):
        raise CardsInvalid(
            [f"branch {branch} already exists; target its pull request instead"]
        )
    stamped = stored_group(
        group, [{**card, "added_at": context.added_at} for card in group["cards"]]
    )
    start_reference = fetch_reference(context.repository_directory, "main")
    write_and_push(
        context,
        branch,
        start_reference,
        stamped,
        f"docs(ril): propose the {group['topic_slug']} group",
    )
    created = context.forge.open_pull_request(
        branch,
        f"{PULL_REQUEST_TITLE_PREFIX}{group['title']}",
        pull_request_body(stamped, branch),
    )
    return {
        **created,
        "branch": branch,
        "added": [card["capture"] for card in group["cards"]],
        "revised": [],
    }
