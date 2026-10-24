from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import forge_review
from review_command_runner import ReviewTargetError

GITLAB_LINK = "https://gitlab.example/group/project/-/merge_requests/7"
WORKTREE_LIST = (
    "worktree /repo\nHEAD abc\nbranch refs/heads/main\n\n"
    "worktree /repo-feature\nHEAD def\nbranch refs/heads/feature\n\n"
    "worktree /tmp/review\nHEAD 123\ndetached\n"
)


@pytest.fixture
def forge_doubles():
    with (
        patch("forge_review.run_git") as run_git,
        patch("forge_review.run_command") as run_command,
        patch("forge_review.subprocess.run") as neovim,
    ):
        run_git.side_effect = lambda arguments: (
            WORKTREE_LIST if arguments[:2] == ["worktree", "list"] else ""
        )
        yield run_git, run_command, neovim


def git_calls(double) -> list[list[str]]:
    return [call.args[0] for call in double.call_args_list]


def test_pull_request_opens_the_octo_review_for_its_url(forge_doubles):
    run_git, _run_command, neovim = forge_doubles
    forge_review.review_on_forge("https://github.com/owner/repo/pull/12", "feature")
    neovim.assert_called_once_with(
        [
            "nvim",
            "+lua require('config.code_review.pull_request_review')"
            ".open('https://github.com/owner/repo/pull/12')",
        ]
    )
    run_git.assert_not_called()


def test_merge_request_reviews_in_the_worktree_that_has_its_branch(forge_doubles):
    run_git, run_command, neovim = forge_doubles
    forge_review.review_on_forge(GITLAB_LINK, "feature")
    assert neovim.call_args.kwargs["cwd"] == Path("/repo-feature")
    assert git_calls(run_git) == [["worktree", "list", "--porcelain"]]
    run_command.assert_not_called()


def test_merge_request_without_local_branch_borrows_one_and_deletes_it_after(
    forge_doubles,
):
    run_git, run_command, neovim = forge_doubles
    run_command.return_value = MagicMock(returncode=1)
    forge_review.review_on_forge(GITLAB_LINK, "someone/topic")
    fetch_call, worktree_add_call = git_calls(run_git)[1:]
    assert fetch_call[-1] == (
        "+refs/heads/someone/topic:refs/remotes/origin/someone/topic"
    )
    assert worktree_add_call[:6] == [
        "worktree",
        "add",
        "--quiet",
        "--track",
        "-b",
        "someone/topic",
    ]
    review_worktree = Path(worktree_add_call[6])
    assert neovim.call_args.kwargs["cwd"] == review_worktree
    assert git_calls(run_command)[-2:] == [
        ["git", "worktree", "remove", "--force", str(review_worktree)],
        ["git", "branch", "--quiet", "-D", "someone/topic"],
    ]


def test_merge_request_on_an_existing_branch_never_deletes_that_branch(
    forge_doubles,
):
    run_git, run_command, neovim = forge_doubles
    run_command.return_value = MagicMock(returncode=0)
    forge_review.review_on_forge(GITLAB_LINK, "mine")
    worktree_add_call = git_calls(run_git)[1]
    assert worktree_add_call[:3] == ["worktree", "add", "--quiet"]
    assert worktree_add_call[-1] == "mine"
    assert not any(call[:2] == ["git", "branch"] for call in git_calls(run_command))


def test_a_failed_review_still_removes_the_borrowed_branch(forge_doubles):
    _run_git, run_command, neovim = forge_doubles
    run_command.return_value = MagicMock(returncode=1)
    neovim.side_effect = KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        forge_review.review_on_forge(GITLAB_LINK, "someone/topic")
    assert git_calls(run_command)[-1] == [
        "git",
        "branch",
        "--quiet",
        "-D",
        "someone/topic",
    ]


def test_a_non_link_is_rejected(forge_doubles):
    with pytest.raises(ReviewTargetError, match="not an MR/PR link"):
        forge_review.review_on_forge("feature", "feature")
