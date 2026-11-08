import json
import subprocess

import pytest

from forge import native, proposal_reading, proposal_writing
from forge.repository import Repository

GITHUB = Repository("github", "github.example", "owner/project")
GITLAB = Repository("gitlab", "gitlab.example", "group/project")


@pytest.fixture
def recorded_commands(monkeypatch):
    commands = []

    def run(command, **options):
        commands.append((command, options.get("input")))
        return subprocess.CompletedProcess(
            command, 0, "https://github.example/owner/project/pull/12\n", ""
        )

    def capture(command, **options):
        commands.append((command, None))
        return {"iid": 5, "web_url": "https://gitlab.example/mr/5"}

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(proposal_writing, "capture_json", capture)
    return commands


def test_github_proposal_writes_pass_the_body_on_standard_input(recorded_commands):
    created = proposal_writing.open_change_request(
        GITHUB, "ril-group-x", "main", "RIL: x", "| table |"
    )
    proposal_writing.comment_on_change_request(GITHUB, 12, "reply")
    proposal_writing.replace_change_request_body(GITHUB, 12, "new body")
    proposal_writing.merge_change_request(GITHUB, 12)

    assert created == {
        "number": 12,
        "url": "https://github.example/owner/project/pull/12",
    }
    assert [command[2] for command, _ in recorded_commands] == [
        "create",
        "comment",
        "edit",
        "merge",
    ]
    assert [body for _, body in recorded_commands] == [
        "| table |",
        "reply",
        "new body",
        None,
    ]
    assert all(
        command[command.index("--repo") + 1] == GITHUB.url
        for command, _ in recorded_commands
    )


def test_gitlab_proposal_writes_use_the_api_with_an_explicit_host(recorded_commands):
    created = proposal_writing.open_change_request(
        GITLAB, "ril-group-x", "main", "RIL: x", "body"
    )
    proposal_writing.comment_on_change_request(GITLAB, 5, "reply")
    proposal_writing.merge_change_request(GITLAB, 5)

    assert created == {"number": 5, "url": "https://gitlab.example/mr/5"}
    endpoints = [command[4] for command, _ in recorded_commands]
    assert endpoints == [
        "projects/group%2Fproject/merge_requests",
        "projects/group%2Fproject/merge_requests/5/notes",
        "projects/group%2Fproject/merge_requests/5/merge",
    ]
    assert all(
        command[-2:] == ["--hostname", "gitlab.example"]
        for command, _ in recorded_commands
    )


def test_gitlab_detail_and_closed_listing_match_the_github_shape(monkeypatch):
    merge_request = {
        "iid": 5,
        "source_branch": "ril-group-x",
        "sha": "abc",
        "state": "merged",
        "title": "t",
        "description": None,
        "web_url": "u",
    }

    def pages(repository, endpoint):
        if "/notes?" in endpoint:
            return [
                {
                    "id": 1,
                    "body": "ok",
                    "created_at": "2026-11-08T13:00:00Z",
                    "system": False,
                }
            ]
        return [
            merge_request,
            {**merge_request, "iid": 6, "state": "opened"},
            {**merge_request, "iid": 7, "source_branch": "feature"},
        ]

    monkeypatch.setattr(proposal_reading, "gitlab_pages", pages)
    monkeypatch.setattr(
        proposal_reading, "gitlab_json", lambda repository, endpoint: merge_request
    )

    detail = proposal_reading.change_request(GITLAB, 5)
    closed = proposal_reading.closed_change_requests(GITLAB, "ril-")

    assert detail["headRefName"] == "ril-group-x" and detail["body"] == ""
    assert detail["comments"] == [
        {"id": 1, "body": "ok", "createdAt": "2026-11-08T13:00:00Z"}
    ]
    assert [proposal["number"] for proposal in closed] == [5]


def test_github_closed_listing_keeps_only_the_prefix(monkeypatch):
    listed = [
        {
            "number": 1,
            "headRefName": "ril-a",
            "title": "",
            "body": "",
            "state": "MERGED",
        },
        {"number": 2, "headRefName": "x", "title": "", "body": "", "state": "CLOSED"},
    ]
    monkeypatch.setattr(native, "capture_json", lambda command, **options: listed)
    monkeypatch.setattr(
        proposal_reading,
        "capture_json",
        lambda command, **options: json.loads(json.dumps(listed)),
    )

    assert [
        proposal["number"]
        for proposal in proposal_reading.closed_change_requests(GITHUB, "ril-")
    ] == [1]
