from unittest.mock import patch

import pytest

import review_target
from change_requests import ChangeRequest
from review_command_runner import ReviewTargetError

MERGE_REQUEST = ChangeRequest(
    title="Title",
    description="",
    web_url="https://example/388",
    base_branch="develop",
    head_fetch_reference="merge-requests/388/head",
)


def fake_fetch_commit(reference: str) -> str:
    return f"commit-of-{reference}"


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
        patch("review_target.fetch_commit", side_effect=fake_fetch_commit),
    ):
        yield


@pytest.mark.parametrize("raw_target", ["388", "!388", "#388", " 388 "])
def test_request_number_reviews_the_fetched_request_head_against_its_target(
    git_doubles, raw_target
):
    with patch(
        "review_target.view_change_request", return_value=MERGE_REQUEST
    ) as view_change_request:
        resolved = review_target.resolve_review_target(raw_target)
    view_change_request.assert_called_once_with("388")
    assert resolved.head_commit == "commit-of-merge-requests/388/head"
    assert resolved.merge_base_commit == (
        "merge-base-of-commit-of-develop-and-commit-of-merge-requests/388/head"
    )
    assert resolved.change_request == MERGE_REQUEST


def test_unknown_request_number_raises(git_doubles):
    with (
        patch("review_target.view_change_request", return_value=None),
        pytest.raises(ReviewTargetError, match="no MR/PR 404"),
    ):
        review_target.resolve_review_target("404")


def test_empty_target_reviews_the_local_current_branch_against_its_request_base(
    git_doubles,
):
    with (
        patch("review_target.view_change_request", return_value=MERGE_REQUEST),
        patch("review_target.local_branch_commit", return_value="local-feature-tip"),
    ):
        resolved = review_target.resolve_review_target("")
    assert resolved.head_commit == "local-feature-tip"
    assert resolved.merge_base_commit == (
        "merge-base-of-commit-of-develop-and-local-feature-tip"
    )


def test_branch_without_request_or_local_copy_uses_the_remote_branch_and_default_base(
    git_doubles,
):
    with (
        patch("review_target.view_change_request", return_value=None),
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
