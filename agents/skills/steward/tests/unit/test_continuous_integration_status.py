import json
from pathlib import Path

from steward_test_helpers import continuous_integration_status

status_for_revision = (
    continuous_integration_status.continuous_integration_status_for_revision
)


def runner_returning(return_code, output):
    return lambda arguments, working_directory, timeout_seconds: (return_code, output)


def runs_payload(*runs):
    return json.dumps(list(runs))


def test_empty_revision_reports_none_without_querying():
    def explode(*_):
        raise AssertionError("must not query gh for an empty revision")

    assert status_for_revision(Path("/repo"), "", explode) == {
        "available": True,
        "state": "none",
    }


def test_missing_gh_binary_marks_unavailable():
    result = status_for_revision(Path("/repo"), "abc", runner_returning(127, ""))
    assert result == {"available": False}


def test_all_completed_success_is_passing():
    payload = runs_payload(
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "workflowName": "tests",
            "url": "u1",
        },
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "workflowName": "Nix Lint",
            "url": "u2",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "passing"
    assert result["failing"] == []


def test_any_failed_workflow_is_failing_with_names_and_urls():
    payload = runs_payload(
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "workflowName": "tests",
            "url": "u1",
        },
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "failure",
            "workflowName": "Nix Lint",
            "url": "u2",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "failing"
    assert result["failing"] == [{"workflow": "Nix Lint", "url": "u2"}]


def test_incomplete_run_is_pending_when_nothing_failed():
    payload = runs_payload(
        {
            "headSha": "abc",
            "status": "in_progress",
            "conclusion": None,
            "workflowName": "tests",
            "url": "u1",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "pending"
    assert result["pending"] == ["tests"]


def test_failure_outranks_pending():
    payload = runs_payload(
        {
            "headSha": "abc",
            "status": "in_progress",
            "conclusion": None,
            "workflowName": "tests",
            "url": "u1",
        },
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "failure",
            "workflowName": "Nix Lint",
            "url": "u2",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "failing"


def test_runs_for_other_revisions_are_ignored():
    payload = runs_payload(
        {
            "headSha": "other",
            "status": "completed",
            "conclusion": "failure",
            "workflowName": "Nix Lint",
            "url": "u1",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "none"


def test_only_latest_run_per_workflow_counts():
    payload = runs_payload(
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "success",
            "workflowName": "Nix Lint",
            "url": "rerun",
        },
        {
            "headSha": "abc",
            "status": "completed",
            "conclusion": "failure",
            "workflowName": "Nix Lint",
            "url": "first",
        },
    )
    result = status_for_revision(Path("/repo"), "abc", runner_returning(0, payload))
    assert result["state"] == "passing"
