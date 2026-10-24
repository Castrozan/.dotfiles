import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from change_requests import ChangeRequest, format_change_request
from review_command_runner import run_command, run_git
from review_target import ReviewTarget

LAZYGIT_SHARE_OF_REVIEW_TAB = "0.65"
FORGE_REVIEW_KEY = "I"


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


def move_review_into_its_own_tab(review_target: ReviewTarget) -> None:
    review_pane_identifier = os.environ.get("HERDR_PANE_ID")
    if not review_pane_identifier:
        return
    run_command(["herdr", "pane", "zoom", review_pane_identifier, "--off"])
    run_command(
        [
            "herdr",
            "pane",
            "move",
            review_pane_identifier,
            "--new-tab",
            "--label",
            f"review {review_target.selector}",
            "--focus",
        ]
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


def forge_review_lazygit_config(change_request: ChangeRequest) -> str:
    forge_review_command = shlex.join(
        [
            sys.executable,
            str(Path(__file__).with_name("review_changes_cli.py")),
            "--forge-review",
            change_request.web_url,
            change_request.head_branch,
        ]
    )
    return (
        "customCommands:\n"
        f"  - key: {FORGE_REVIEW_KEY}\n"
        "    context: global\n"
        "    output: terminal\n"
        "    description: Comment on and review this MR/PR in Neovim\n"
        f"    command: {json.dumps(forge_review_command)}\n"
    )


def lazygit_arguments(extra_config_file: Path | None) -> list[str]:
    if extra_config_file is None:
        return ["lazygit"]
    user_config_directory = run_command(["lazygit", "--print-config-dir"]).stdout
    user_config_file = Path(user_config_directory.strip()) / "config.yml"
    config_files = [user_config_file] if user_config_file.exists() else []
    config_files.append(extra_config_file)
    return [
        "lazygit",
        "--use-config-file",
        ",".join(str(config_file) for config_file in config_files),
    ]


def review_in_lazygit(review_target: ReviewTarget) -> None:
    review_directory = Path(tempfile.mkdtemp(prefix="review-changes-"))
    worktree_directory = review_directory / "worktree"
    description_pane_identifier = None
    forge_review_config_file = None
    try:
        prepare_review_worktree(review_target, worktree_directory)
        move_review_into_its_own_tab(review_target)
        if review_target.change_request:
            description_file = review_directory / "description.md"
            description_file.write_text(
                format_change_request(review_target.change_request)
            )
            description_pane_identifier = open_description_pane(description_file)
            forge_review_config_file = review_directory / "forge-review.yml"
            forge_review_config_file.write_text(
                forge_review_lazygit_config(review_target.change_request)
            )
        subprocess.run(
            lazygit_arguments(forge_review_config_file), cwd=worktree_directory
        )
    finally:
        run_command(["git", "worktree", "remove", "--force", str(worktree_directory)])
        shutil.rmtree(review_directory, ignore_errors=True)
        if description_pane_identifier:
            run_command(["herdr", "pane", "close", description_pane_identifier])
