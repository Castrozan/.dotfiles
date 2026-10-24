import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from change_requests import format_change_request
from review_command_runner import run_command, run_git
from review_target import ReviewTarget

LAZYGIT_SHARE_OF_REVIEW_TAB = "0.65"


def prepare_review_worktree(
    review_target: ReviewTarget, worktree_directory: Path
) -> None:
    run_git(
        [
            "worktree",
            "add",
            "--detach",
            "--quiet",
            str(worktree_directory),
            review_target.head_commit,
        ]
    )
    run_git(
        ["reset", "--quiet", "--soft", review_target.merge_base_commit],
        worktree_directory,
    )


def open_description_pane(description_file: Path) -> str | None:
    review_pane_identifier = os.environ.get("HERDR_PANE_ID")
    if not review_pane_identifier:
        return None
    split_result = run_command(
        [
            "herdr",
            "pane",
            "split",
            review_pane_identifier,
            "--direction",
            "right",
            "--ratio",
            LAZYGIT_SHARE_OF_REVIEW_TAB,
            "--no-focus",
            "--cwd",
            str(description_file.parent),
        ]
    )
    if split_result.returncode != 0:
        return None
    description_pane_identifier = json.loads(split_result.stdout)["result"]["pane"][
        "pane_id"
    ]
    run_command(
        [
            "herdr",
            "pane",
            "run",
            description_pane_identifier,
            f"less {description_file.name}",
        ]
    )
    return description_pane_identifier


def review_in_lazygit(review_target: ReviewTarget) -> None:
    review_directory = Path(tempfile.mkdtemp(prefix="review-changes-"))
    worktree_directory = review_directory / "worktree"
    description_pane_identifier = None
    try:
        prepare_review_worktree(review_target, worktree_directory)
        if review_target.change_request:
            description_file = review_directory / "description.md"
            description_file.write_text(
                format_change_request(review_target.change_request)
            )
            description_pane_identifier = open_description_pane(description_file)
        subprocess.run(["lazygit"], cwd=worktree_directory)
    finally:
        run_command(["git", "worktree", "remove", "--force", str(worktree_directory)])
        shutil.rmtree(review_directory, ignore_errors=True)
        if description_pane_identifier:
            run_command(["herdr", "pane", "close", description_pane_identifier])
