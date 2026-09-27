import pytest

import workflow_context as CONTEXT


def test_partial_retry_retains_the_original_job_artifact(run, artifact, monkeypatch):
    original = {
        **run,
        "run_attempt": 1,
        "run_started_at": "2026-09-26T00:00:00Z",
        "updated_at": "2026-09-26T00:09:00Z",
    }
    retained = {
        "id": 987,
        "name": "quick-tests",
        "run_id": run["id"],
        "head_sha": run["head_sha"],
        "status": "completed",
        "started_at": "2026-09-26T00:01:00Z",
        "completed_at": "2026-09-26T00:05:00Z",
        "steps": [
            {
                "name": "Retain native Bats test results",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-09-26T00:01:59Z",
                "completed_at": "2026-09-26T00:02:01Z",
            }
        ],
    }
    artifact["created_at"] = "2026-09-26T00:02:00Z"
    route = f"repos/{CONTEXT.REPOSITORY}/actions/runs/123"
    documents = {
        f"{route}/attempts/2": run,
        f"{route}/attempts/1": original,
        f"{route}/attempts/2/jobs?per_page=100": {"total_count": 1, "jobs": [retained]},
        f"{route}/artifacts?per_page=100": {"total_count": 1, "artifacts": [artifact]},
    }
    monkeypatch.setattr(CONTEXT, "github_document", documents.__getitem__)
    context = CONTEXT.collect_context({"workflow_run": run})
    selected = context["artifacts"]["bats-junit"]
    assert selected["id"] == 456
    assert selected["producer"]["runAttempt"] == 1
    assert context["workflow"]["runAttempt"] == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"head_sha": "b" * 40},
        {"run_id": 999},
        {"status": "in_progress"},
        {"completed_at": "2026-09-26T00:11:00Z"},
        {"started_at": None},
    ],
)
def test_foreign_or_incomplete_job_cannot_authorize_an_artifact(
    run, artifact, jobs, changes
):
    jobs[0].update(changes)
    context = CONTEXT.build_context(run, jobs, [artifact])
    assert context["artifacts"]["bats-junit"]["id"] is None


def test_retried_job_cannot_reuse_an_earlier_attempt_artifact(run, artifact, jobs):
    original = CONTEXT.workflow_identity(
        {
            **run,
            "run_attempt": 1,
            "run_started_at": "2026-09-26T00:00:00Z",
            "updated_at": "2026-09-26T00:09:00Z",
        }
    )
    artifact["created_at"] = "2026-09-26T00:02:00Z"
    context = CONTEXT.build_context(
        run, jobs, [artifact], [original, CONTEXT.workflow_identity(run)]
    )
    assert context["artifacts"]["bats-junit"]["id"] is None


def test_artifact_must_match_its_upload_step_not_merely_its_job(run, artifact, jobs):
    artifact["created_at"] = "2026-09-26T00:15:00Z"
    context = CONTEXT.build_context(run, jobs, [artifact])
    assert context["artifacts"]["bats-junit"]["id"] is None
