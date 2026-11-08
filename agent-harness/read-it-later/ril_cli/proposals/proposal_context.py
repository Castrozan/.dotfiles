from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forge_adapter import ForgeAdapter
from proposals.decision_files import render_decision_file, render_summary
from proposals.git_worktrees import branch_worktree, commit_and_push
from pull_requests import decision_path_for_branch

PULL_REQUEST_TITLE_PREFIX = "RIL: "


@dataclass(frozen=True)
class ProposalContext:
    repository_directory: Path
    inbox_directory: Path
    forge: ForgeAdapter
    now: datetime

    @property
    def added_at(self) -> str:
        return self.now.astimezone(timezone.utc).isoformat(timespec="seconds")

    @property
    def proposal_date(self) -> str:
        return self.now.astimezone().date().isoformat()


def stored_group(group: dict, cards: list[dict]) -> dict:
    kept_fields = {
        name: value
        for name, value in group.items()
        if name not in ("target_pull_request", "cards")
    }
    return {**kept_fields, "cards": cards}


def write_and_push(
    context: ProposalContext,
    branch: str,
    start_reference: str,
    group: dict,
    message: str,
) -> None:
    decision_path = decision_path_for_branch(branch)
    with branch_worktree(
        context.repository_directory, branch, start_reference
    ) as worktree_path:
        (worktree_path / decision_path).parent.mkdir(parents=True, exist_ok=True)
        (worktree_path / decision_path).write_text(
            render_decision_file(group), encoding="utf-8"
        )
        commit_and_push(worktree_path, decision_path, message, branch)


def pull_request_body(group: dict, branch: str) -> str:
    return f"{render_summary(group)}\nDecision file: `{decision_path_for_branch(branch)}`\n"
