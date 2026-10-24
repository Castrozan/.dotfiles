import shutil
import subprocess
import tempfile
from pathlib import Path

from request_links import parse_request_link
from review_command_runner import ReviewTargetError, run_command, run_git

PULL_REQUEST_REVIEW_MODULE = "config.code_review.pull_request_review"


def worktree_with_branch_checked_out(branch: str) -> Path | None:
    worktree_directory = None
    for line in run_git(["worktree", "list", "--porcelain"]).splitlines():
        if line.startswith("worktree "):
            worktree_directory = Path(line.removeprefix("worktree "))
        if line == f"branch refs/heads/{branch}":
            return worktree_directory
    return None


def local_branch_exists(branch: str) -> bool:
    result = run_command(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"]
    )
    return result.returncode == 0


def review_pull_request_in_neovim(web_url: str) -> None:
    subprocess.run(
        ["nvim", f"+lua require('{PULL_REQUEST_REVIEW_MODULE}').open('{web_url}')"]
    )


def review_merge_request_in_neovim(review_directory: Path) -> None:
    subprocess.run(["nvim", "+lua require('gitlab').review()"], cwd=review_directory)


def review_merge_request_on_its_branch(source_branch: str) -> None:
    checked_out_directory = worktree_with_branch_checked_out(source_branch)
    if checked_out_directory:
        review_merge_request_in_neovim(checked_out_directory)
        return
    branch_was_created = not local_branch_exists(source_branch)
    review_directory = Path(tempfile.mkdtemp(prefix="review-changes-forge-"))
    branch_worktree = review_directory / "worktree"
    try:
        if branch_was_created:
            run_git(
                [
                    "fetch",
                    "--quiet",
                    "origin",
                    f"+refs/heads/{source_branch}:refs/remotes/origin/{source_branch}",
                ]
            )
            run_git(
                [
                    "worktree",
                    "add",
                    "--quiet",
                    "--track",
                    "-b",
                    source_branch,
                    str(branch_worktree),
                    f"origin/{source_branch}",
                ]
            )
        else:
            run_git(["worktree", "add", "--quiet", str(branch_worktree), source_branch])
        review_merge_request_in_neovim(branch_worktree)
    finally:
        run_command(["git", "worktree", "remove", "--force", str(branch_worktree)])
        shutil.rmtree(review_directory, ignore_errors=True)
        if branch_was_created:
            run_command(["git", "branch", "--quiet", "-D", source_branch])


def review_on_forge(web_url: str, source_branch: str) -> None:
    request_link = parse_request_link(web_url)
    if request_link is None:
        raise ReviewTargetError(f"not an MR/PR link: {web_url}")
    if request_link.repository.is_github:
        review_pull_request_in_neovim(web_url)
        return
    review_merge_request_on_its_branch(source_branch)
