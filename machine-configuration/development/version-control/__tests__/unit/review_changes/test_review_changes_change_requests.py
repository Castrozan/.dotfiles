import json
from unittest.mock import MagicMock, patch

import pytest

import change_requests
from review_command_runner import ReviewTargetError


def completed_process(returncode: int, stdout: str = "") -> MagicMock:
    process = MagicMock()
    process.returncode = returncode
    process.stdout = stdout
    return process


class TestViewGithubPullRequest:
    def test_maps_pull_request_fields_and_fetches_the_pull_head(self):
        pull_request = {
            "number": 12,
            "title": "Add review launcher",
            "body": None,
            "url": "https://github.com/owner/repository/pull/12",
            "baseRefName": "main",
        }
        with patch(
            "change_requests.run_command",
            return_value=completed_process(0, json.dumps(pull_request)),
        ):
            change_request = change_requests.view_github_pull_request("12")
        assert change_request == change_requests.ChangeRequest(
            title="Add review launcher",
            description="",
            web_url="https://github.com/owner/repository/pull/12",
            base_branch="main",
            head_fetch_reference="pull/12/head",
        )

    def test_lookup_failure_raises_the_cli_message_on_one_line(self):
        failed_lookup = completed_process(1)
        failed_lookup.stderr = "  ERROR\n\n  dial tcp 10.0.0.1:443:\n  i/o timeout.\n"
        with (
            patch("change_requests.run_command", return_value=failed_lookup),
            pytest.raises(
                ReviewTargetError, match="^ERROR dial tcp 10.0.0.1:443: i/o timeout.$"
            ),
        ):
            change_requests.view_github_pull_request("12")

    def test_lookup_failure_without_cli_message_names_the_missing_request(self):
        failed_lookup = completed_process(1)
        failed_lookup.stderr = ""
        with (
            patch("change_requests.run_command", return_value=failed_lookup),
            pytest.raises(ReviewTargetError, match="no MR/PR missing found"),
        ):
            change_requests.view_gitlab_merge_request("missing")


class TestViewGitlabMergeRequest:
    def test_maps_merge_request_fields_and_fetches_the_merge_request_head(self):
        merge_request = {
            "iid": 388,
            "title": "feat: auditoria",
            "description": "Body",
            "web_url": "https://gitlab.example/group/project/-/merge_requests/388",
            "target_branch": "main",
        }
        with patch(
            "change_requests.run_command",
            return_value=completed_process(0, json.dumps(merge_request)),
        ) as run_command:
            change_request = change_requests.view_gitlab_merge_request("388")
        run_command.assert_called_once_with(
            ["glab", "mr", "view", "388", "--output", "json"]
        )
        assert change_request.head_fetch_reference == "merge-requests/388/head"
        assert change_request.base_branch == "main"
        assert change_request.description == "Body"


class TestViewChangeRequest:
    def test_routes_github_origins_to_gh(self):
        with (
            patch("change_requests.run_git", return_value="git@github.com:o/r.git"),
            patch("change_requests.view_github_pull_request") as view_github,
            patch("change_requests.view_gitlab_merge_request") as view_gitlab,
        ):
            change_requests.view_change_request("5")
        view_github.assert_called_once_with("5")
        view_gitlab.assert_not_called()

    def test_routes_every_other_origin_to_glab(self):
        with (
            patch(
                "change_requests.run_git",
                return_value="git@gitlab.services.example:group/project.git",
            ),
            patch("change_requests.view_github_pull_request") as view_github,
            patch("change_requests.view_gitlab_merge_request") as view_gitlab,
        ):
            change_requests.view_change_request("5")
        view_gitlab.assert_called_once_with("5")
        view_github.assert_not_called()


def test_format_change_request_puts_title_link_and_description_in_order():
    change_request = change_requests.ChangeRequest(
        title="Title",
        description="Description",
        web_url="https://example/1",
        base_branch="main",
        head_fetch_reference="pull/1/head",
    )
    assert (
        change_requests.format_change_request(change_request)
        == "# Title\n\nhttps://example/1\n\nDescription\n"
    )
