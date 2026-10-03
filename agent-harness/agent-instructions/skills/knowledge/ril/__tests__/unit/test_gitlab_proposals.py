import json
from pathlib import Path
import subprocess

from forge.repository import Repository
from pull_requests import open_ril_pull_requests, unanswered_response_fingerprint


def test_gitlab_discussion_resumes_only_after_a_new_human_comment(monkeypatch):
    monkeypatch.setattr(
        "pull_requests.resolve_repository",
        lambda _: Repository("gitlab", "gitlab.com", "owner/project"),
    )
    comments = [
        {"id": 1, "body": "why?", "created_at": "first"},
        {"id": 2, "body": "answered\n<!-- ril-watcher -->", "created_at": "second"},
    ]

    def execute(command, **options):
        response = (
            comments
            if "/notes?" in command[2]
            else [{"iid": 7, "source_branch": "ril-example"}]
        )
        assert command[0] == "glab"
        assert command[-2:] == ["--hostname", "gitlab.com"]
        return subprocess.CompletedProcess(command, 0, json.dumps(response))

    monkeypatch.setattr(subprocess, "run", execute)
    assert (
        unanswered_response_fingerprint(open_ril_pull_requests(Path("/repo"))[0]) == ""
    )
    comments.append({"id": 3, "body": "another question", "created_at": "third"})
    assert (
        unanswered_response_fingerprint(open_ril_pull_requests(Path("/repo"))[0])
        == "7:3"
    )
