from unittest.mock import patch

import pytest

import review_target
from change_requests import ChangeRequest
from request_links import ForgeRepository, RequestLink
from review_command_runner import ReviewTargetError

CURRENT_REPOSITORY = ForgeRepository("gitlab.example", "group/current")
LINKED_REPOSITORY = ForgeRepository("gitlab.example", "group/linked")
MERGE_REQUEST = ChangeRequest(
    title="Title",
    description="",
    web_url="https://example/388",
    base_branch="develop",
    head_branch="feature",
    head_fetch_reference="merge-requests/388/head",
)


def fake_fetch_commits(*references: str) -> list[str]:
    return [f"commit-of-{reference}" for reference in references]


def fake_run_git(arguments: list[str], working_directory=None) -> str:
    if arguments == ["branch", "--show-current"]:
        return "feature"
    if arguments[0] == "merge-base":
        return f"merge-base-of-{arguments[1]}-and-{arguments[2]}"
    raise AssertionError(f"unexpected git call {arguments}")


@pytest.fixture
def git_doubles():
    with (
        patch("review_target.run_git", side_effect=fake_run_git),
        patch("review_target.fetch_commits", side_effect=fake_fetch_commits),
        patch("review_target.origin_repository", return_value=CURRENT_REPOSITORY),
        patch("review_target.enter_local_clone") as enter_local_clone,
    ):
        yield enter_local_clone


@pytest.mark.parametrize("raw_target", ["388", "!388", "#388", " 388 "])
def test_request_number_reviews_the_current_repository_request_against_its_target(
    git_doubles, raw_target
):
    with patch(
        "review_target.view_change_request", return_value=MERGE_REQUEST
    ) as view_change_request:
        resolved = review_target.resolve_review_target(raw_target)
    view_change_request.assert_called_once_with(CURRENT_REPOSITORY, "388")
    git_doubles.assert_called_once_with(CURRENT_REPOSITORY)
    assert resolved.selector == "!388"
    assert resolved.head_commit == "commit-of-merge-requests/388/head"
    assert resolved.merge_base_commit == (
        "merge-base-of-commit-of-develop-and-commit-of-merge-requests/388/head"
    )
    assert resolved.change_request == MERGE_REQUEST


def test_request_link_looks_up_the_linked_repository_not_the_current_one(git_doubles):
    with patch(
        "review_target.view_change_request", return_value=MERGE_REQUEST
    ) as view_change_request:
        review_target.resolve_review_target(
            "https://gitlab.example/group/linked/-/merge_requests/388"
        )
    view_change_request.assert_called_once_with(LINKED_REPOSITORY, "388")
    git_doubles.assert_called_once_with(LINKED_REPOSITORY)


def test_empty_target_reviews_the_detected_request_instead_of_the_branch(
    git_doubles,
):
    detected_request = RequestLink(LINKED_REPOSITORY, "7")
    with patch(
        "review_target.view_change_request", return_value=MERGE_REQUEST
    ) as view_change_request:
        resolved = review_target.resolve_review_target(" ", detected_request)
    view_change_request.assert_called_once_with(LINKED_REPOSITORY, "7")
    assert resolved.selector == "!7"


def test_typed_target_wins_over_the_detected_request(git_doubles):
    with patch(
        "review_target.view_change_request", return_value=MERGE_REQUEST
    ) as view_change_request:
        review_target.resolve_review_target("12", RequestLink(LINKED_REPOSITORY, "7"))
    view_change_request.assert_called_once_with(CURRENT_REPOSITORY, "12")


def test_request_number_outside_a_repository_asks_for_the_link(git_doubles):
    with (
        patch("review_target.origin_repository", return_value=None),
        pytest.raises(ReviewTargetError, match="paste the MR/PR link"),
    ):
        review_target.resolve_review_target("388")


def test_request_lookup_failure_surfaces_the_forge_message(git_doubles):
    with (
        patch(
            "review_target.view_change_request",
            side_effect=ReviewTargetError("dial tcp 10.0.0.1:443: i/o timeout"),
        ),
        pytest.raises(ReviewTargetError, match="i/o timeout"),
    ):
        review_target.resolve_review_target("404")


def test_empty_target_reviews_the_local_current_branch_against_its_request_base(
    git_doubles,
):
    with (
        patch(
            "review_target.view_change_request", return_value=MERGE_REQUEST
        ) as view_change_request,
        patch("review_target.local_branch_commit", return_value="local-feature-tip"),
    ):
        resolved = review_target.resolve_review_target("")
    view_change_request.assert_called_once_with(CURRENT_REPOSITORY, "feature")
    assert resolved.head_commit == "local-feature-tip"
    assert resolved.merge_base_commit == (
        "merge-base-of-commit-of-develop-and-local-feature-tip"
    )


def test_branch_without_request_or_local_copy_uses_the_remote_branch_and_default_base(
    git_doubles,
):
    with (
        patch(
            "review_target.view_change_request",
            side_effect=ReviewTargetError("no merge request for branch"),
        ),
        patch("review_target.local_branch_commit", return_value=None),
        patch("review_target.default_base_branch", return_value="main"),
    ):
        resolved = review_target.resolve_review_target("someone/branch")
    assert resolved.head_commit == "commit-of-someone/branch"
    assert resolved.merge_base_commit == (
        "merge-base-of-commit-of-main-and-commit-of-someone/branch"
    )
    assert resolved.change_request is None


def test_detached_head_without_target_raises():
    with (
        patch("review_target.run_git", return_value=""),
        pytest.raises(ReviewTargetError, match="detached"),
    ):
        review_target.resolve_review_target("")


def test_one_fetch_returns_each_reference_commit_in_request_order(tmp_path):
    fetch_head = tmp_path / "FETCH_HEAD"
    fetch_head.write_text(
        "head-commit\t\t'refs/pull/236/head' of github.com:owner/repo\n"
        "base-commit\t\tbranch 'main' of github.com:owner/repo\n"
    )
    with patch("review_target.run_git", side_effect=["", str(fetch_head)]) as run_git:
        commits = review_target.fetch_commits("pull/236/head", "main")
    assert run_git.call_args_list[0].args[0] == [
        "fetch",
        "--quiet",
        "origin",
        "pull/236/head",
        "main",
    ]
    assert commits == ["head-commit", "base-commit"]
