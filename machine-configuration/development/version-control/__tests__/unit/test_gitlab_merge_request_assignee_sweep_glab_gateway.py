import json
import subprocess
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

import gitlab_merge_request_assignee_sweep as sweep

MOMENT = datetime(2026, 11, 9, 18, 0, tzinfo=UTC)


def merge_request(internal_id, author_id=7, assignee_ids=()):
    return sweep.MergeRequest(
        project_id=1,
        internal_id=internal_id,
        author_id=author_id,
        assignee_ids=tuple(assignee_ids),
        web_url=f"https://gitlab.example/mr/{internal_id}",
    )


def glab_invocations(monkeypatch, returncode=0, stdout="[]", stderr=""):
    invocations = []

    def fake_run(command, **_):
        invocations.append(command)
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    monkeypatch.setattr(sweep.subprocess, "run", fake_run)
    return invocations


def test_listing_asks_the_server_for_open_unassigned_merge_requests_by_me(monkeypatch):
    invocations = glab_invocations(monkeypatch)

    sweep.GlabMergeRequestGateway("gitlab.example").list_unassigned_authored_since(
        MOMENT
    )

    command = invocations[0]
    assert command[:4] == ["glab", "api", "--hostname", "gitlab.example"]
    query = parse_qs(urlsplit(command[4]).query)
    assert query == {
        "scope": ["created_by_me"],
        "state": ["opened"],
        "assignee_id": ["None"],
        "created_after": [MOMENT.isoformat()],
        "per_page": ["100"],
    }


def test_assignment_is_a_put_on_the_merge_request_with_the_author(monkeypatch):
    invocations = glab_invocations(monkeypatch, stdout="{}")

    sweep.GlabMergeRequestGateway("gitlab.example").assign(merge_request(9), 7)

    assert invocations[0][4:] == [
        "-X",
        "PUT",
        "projects/1/merge_requests/9",
        "-F",
        "assignee_id=7",
    ]


def test_read_parses_assignees_from_the_api(monkeypatch):
    payload = {
        "project_id": 1,
        "iid": 9,
        "author": {"id": 7},
        "assignees": [{"id": 8}],
        "web_url": "https://gitlab.example/mr/9",
    }
    glab_invocations(monkeypatch, stdout=json.dumps(payload))

    current = sweep.GlabMergeRequestGateway("gitlab.example").read(merge_request(9))

    assert current == merge_request(9, 7, (8,))


@pytest.mark.parametrize(
    "completed",
    [
        {"returncode": 1, "stderr": "401 Unauthorized"},
        {"returncode": 0, "stdout": "not json"},
    ],
)
def test_glab_failure_becomes_a_request_failure(monkeypatch, completed):
    glab_invocations(monkeypatch, **completed)

    with pytest.raises(sweep.GitLabRequestFailed):
        sweep.GlabMergeRequestGateway("gitlab.example").read(merge_request(9))


def test_glab_timeout_becomes_a_request_failure(monkeypatch):
    def timing_out(command, **_):
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(sweep.subprocess, "run", timing_out)

    with pytest.raises(sweep.GitLabRequestFailed):
        sweep.GlabMergeRequestGateway("gitlab.example").read(merge_request(9))
