import json
from unittest.mock import MagicMock, patch

import pytest

import change_requests
from request_links import ForgeRepository
from review_command_runner import ReviewTargetError

GITHUB_REPOSITORY = ForgeRepository("github.com", "owner/repository")
GITLAB_REPOSITORY = ForgeRepository("gitlab.example", "group/project")


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
            "headRefName": "feature",
        }
        with patch(
            "change_requests.run_command",
            return_value=completed_process(0, json.dumps(pull_request)),
        ) as run_command:
            change_request = change_requests.view_github_pull_request(
                GITHUB_REPOSITORY, "12"
            )
        assert run_command.call_args.args[0][:6] == [
            "gh",
            "pr",
            "view",
            "12",
            "--repo",
            "github.com/owner/repository",
        ]
        assert change_request == change_requests.ChangeRequest(
            title="Add review launcher",
            description="",
            web_url="https://github.com/owner/repository/pull/12",
            base_branch="main",
            head_branch="feature",
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
            change_requests.view_github_pull_request(GITHUB_REPOSITORY, "12")

    def test_lookup_failure_without_cli_message_names_the_missing_request(self):
        failed_lookup = completed_process(1)
        failed_lookup.stderr = ""
        with (
            patch("change_requests.run_command", return_value=failed_lookup),
            pytest.raises(ReviewTargetError, match="no MR/PR missing found"),
        ):
            change_requests.view_gitlab_merge_request(GITLAB_REPOSITORY, "missing")


class TestViewGitlabMergeRequest:
    def test_maps_merge_request_fields_and_fetches_the_merge_request_head(self):
        merge_request = {
            "iid": 388,
            "title": "feat: auditoria",
            "description": "Body",
            "web_url": "https://gitlab.example/group/project/-/merge_requests/388",
            "target_branch": "main",
            "source_branch": "feat/auditoria",
        }
        with patch(
            "change_requests.run_command",
            return_value=completed_process(0, json.dumps(merge_request)),
        ) as run_command:
            change_request = change_requests.view_gitlab_merge_request(
                GITLAB_REPOSITORY, "388"
            )
        run_command.assert_called_once_with(
            [
                "glab",
                "mr",
                "view",
                "388",
                "--repo",
                "https://gitlab.example/group/project",
                "--output",
                "json",
            ]
        )
        assert change_request.head_branch == "feat/auditoria"
        assert change_request.head_fetch_reference == "merge-requests/388/head"
        assert change_request.base_branch == "main"
        assert change_request.description == "Body"


class TestViewChangeRequest:
    def test_routes_github_repositories_to_gh(self):
        with (
            patch("change_requests.view_github_pull_request") as view_github,
            patch("change_requests.view_gitlab_merge_request") as view_gitlab,
        ):
            change_requests.view_change_request(GITHUB_REPOSITORY, "5")
        view_github.assert_called_once_with(GITHUB_REPOSITORY, "5")
        view_gitlab.assert_not_called()

    def test_routes_every_other_repository_to_glab(self):
        with (
            patch("change_requests.view_github_pull_request") as view_github,
            patch("change_requests.view_gitlab_merge_request") as view_gitlab,
        ):
            change_requests.view_change_request(GITLAB_REPOSITORY, "5")
        view_gitlab.assert_called_once_with(GITLAB_REPOSITORY, "5")
        view_github.assert_not_called()


def test_format_change_request_puts_title_branches_link_and_description_in_order():
    change_request = change_requests.ChangeRequest(
        title="Title",
        description="Description",
        web_url="https://example/1",
        base_branch="main",
        head_branch="feature",
        head_fetch_reference="pull/1/head",
    )
    assert (
        change_requests.format_change_request(change_request)
        == "# Title\n\nfeature -> main\nhttps://example/1\n\nDescription\n"
    )
