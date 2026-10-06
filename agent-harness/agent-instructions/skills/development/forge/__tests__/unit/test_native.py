import subprocess

import pytest

from forge import native
from forge.repository import Repository

REPOSITORY = Repository("gitlab", "gitlab.example", "group/subgroup/project")
REVISION = "a" * 40


@pytest.mark.parametrize(
    "state,conclusion",
    [
        ("success", "success"),
        ("failed", "failed"),
        ("canceled", "canceled"),
        ("skipped", "skipped"),
        ("running", None),
        ("manual", None),
    ],
)
def test_pipeline_status_preserves_terminal_and_pending_states(state, conclusion):
    result = native.pipeline_result(
        {
            "id": 7,
            "sha": REVISION,
            "status": state,
            "web_url": "https://gitlab.example/pipeline/7",
        }
    )
    assert result["conclusion"] == conclusion
    assert (result["status"] == "completed") == (conclusion is not None)


def test_unknown_pipeline_state_is_not_success():
    with pytest.raises(ValueError, match="Unknown"):
        native.pipeline_result({"status": "unknown"})


def test_gitlab_queries_use_explicit_host_and_encoded_namespace(monkeypatch):
    calls = []
    monkeypatch.setattr(
        native, "capture_json", lambda command, **options: calls.append(command) or []
    )
    assert native.runs_for_revision(REPOSITORY, REVISION) == []
    assert calls == [
        [
            "glab",
            "api",
            f"projects/group%2Fsubgroup%2Fproject/pipelines?sha={REVISION}&per_page=100&page=1",
            "--hostname",
            "gitlab.example",
        ]
    ]


def test_short_revision_is_rejected_before_network_lookup(monkeypatch):
    monkeypatch.setattr(
        native,
        "capture_json",
        lambda *args, **options: pytest.fail("short SHA reached API"),
    )
    with pytest.raises(ValueError, match="full commit SHA"):
        native.runs_for_revision(REPOSITORY, "abc123")


def test_pagination_fetches_every_page_and_refuses_incomplete_results(monkeypatch):
    pages = iter([list(range(100)), [100]])
    monkeypatch.setattr(native, "gitlab_json", lambda *args, **options: next(pages))
    assert native.gitlab_pages(REPOSITORY, "projects/1/jobs") == list(range(101))
    monkeypatch.setattr(
        native, "gitlab_json", lambda *args, **options: list(range(100))
    )
    with pytest.raises(RuntimeError, match="incomplete"):
        native.gitlab_pages(REPOSITORY, "projects/1/jobs")


def test_pagination_obeys_the_watcher_deadline(monkeypatch):
    monkeypatch.setattr(native.time, "monotonic", lambda: 20)
    with pytest.raises(subprocess.TimeoutExpired):
        native.gitlab_pages(REPOSITORY, "projects/1/jobs", deadline=10)


def test_merge_request_discussion_ignores_system_notes_and_other_branches(monkeypatch):
    calls = []

    def pages(repository, endpoint):
        calls.append(endpoint)
        if "/notes?" in endpoint:
            return [
                {
                    "id": 1,
                    "body": "changed status",
                    "created_at": "earlier",
                    "system": True,
                },
                {
                    "id": 2,
                    "body": "why this approach?",
                    "created_at": "later",
                    "system": False,
                },
            ]
        return [
            {"iid": 9, "source_branch": "ril-capture"},
            {"iid": 10, "source_branch": "other"},
        ]

    monkeypatch.setattr(native, "gitlab_pages", pages)
    result = native.open_change_requests(REPOSITORY, "ril-")
    assert result == [
        {
            "number": 9,
            "headRefName": "ril-capture",
            "comments": [{"id": 2, "body": "why this approach?", "createdAt": "later"}],
        }
    ]
    assert len(calls) == 2
    assert calls[1].endswith("/9/notes?sort=asc&order_by=created_at")


def test_github_queries_use_explicit_repository_url(monkeypatch):
    calls = []
    monkeypatch.setattr(
        native, "capture_json", lambda command: calls.append(command) or []
    )
    repository = Repository("github", "github.example", "owner/project")
    native.runs_for_revision(repository, REVISION)
    native.open_change_requests(repository, "ril-")
    assert all(
        command[command.index("--repo") + 1] == repository.url for command in calls
    )
