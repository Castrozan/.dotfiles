import copy

import pytest

import workflow_context as CONTEXT


def test_failed_workflow_retains_available_evidence_and_missing_inventory(
    run, artifact, jobs
):
    context = CONTEXT.build_context(run, jobs, [artifact])
    assert context["workflow"]["conclusion"] == "failure"
    assert context["workflow"]["runAttempt"] == 2
    assert context["artifacts"]["bats-junit"]["id"] == 456
    assert context["artifacts"]["bats-junit"]["producer"]["runAttempt"] == 2
    assert context["artifacts"]["python-junit"]["id"] is None
    assert context["artifacts"]["python-junit"]["reason"]


@pytest.mark.parametrize(
    "changes",
    [
        {"created_at": "2026-09-26T00:02:00Z"},
        {"created_at": "2026-09-26T00:21:00Z"},
        {"workflow_run": {"id": 123, "head_sha": "b" * 40}},
        {"workflow_run": {"id": 999, "head_sha": "a" * 40}},
        {"expired": True},
    ],
)
def test_artifacts_from_other_attempts_or_subjects_never_become_current(
    run, artifact, jobs, changes
):
    artifact.update(changes)
    context = CONTEXT.build_context(run, jobs, [artifact])
    assert context["artifacts"]["bats-junit"]["id"] is None
    assert context["artifacts"]["bats-junit"]["reason"]


def test_duplicate_named_artifacts_are_ambiguous(run, artifact, jobs):
    duplicate = {**artifact, "id": 789}
    context = CONTEXT.build_context(run, jobs, [artifact, duplicate])
    assert "found 2" in context["artifacts"]["bats-junit"]["reason"]


@pytest.mark.parametrize(
    "changes",
    [
        {"event": "pull_request"},
        {"head_branch": "feature"},
        {"status": "in_progress"},
        {"path": ".github/workflows/foreign.yml"},
        {"head_sha": "abc123"},
        {"head_repository": {"full_name": "foreign/repository"}},
        {"run_attempt": 0},
        {"updated_at": "2026-09-26T00:09:00Z"},
    ],
)
def test_non_producing_run_is_rejected(run, changes):
    run.update(changes)
    with pytest.raises(ValueError):
        CONTEXT.build_context(run, [], [])


def test_changed_run_and_incomplete_pagination_are_rejected(run, monkeypatch):
    changed = copy.deepcopy(run)
    changed["head_sha"] = "b" * 40
    monkeypatch.setattr(CONTEXT, "github_document", lambda route: changed)
    with pytest.raises(ValueError, match="changed"):
        CONTEXT.collect_context({"workflow_run": run})
    with pytest.raises(ValueError, match="Incomplete"):
        CONTEXT.complete_page({"total_count": 101, "jobs": []}, "jobs")


@pytest.mark.parametrize("metadata_state", ["pending", "in_progress", "empty", "job"])
def test_completed_run_waits_for_producer_step_metadata(
    run, artifact, jobs, monkeypatch, metadata_state
):
    jobs[0]["conclusion"] = "success"
    jobs[0]["steps"][0]["status"] = "completed"
    delayed = copy.deepcopy(jobs)
    if metadata_state == "job":
        delayed[0]["status"] = "in_progress"
    elif metadata_state == "empty":
        delayed[0]["steps"] = []
    else:
        delayed[0]["steps"][0].update(
            status=metadata_state, conclusion=None, completed_at=None
        )
    route = f"repos/{CONTEXT.REPOSITORY}/actions/runs/{run['id']}"
    inventories = iter([delayed, jobs])
    calls = []
    waits = []

    def github_document(endpoint):
        calls.append(endpoint)
        if endpoint == f"{route}/attempts/2":
            return run
        if endpoint.endswith("/jobs?per_page=100"):
            return {"total_count": 1, "jobs": next(inventories)}
        return {"total_count": 1, "artifacts": [artifact]}

    monkeypatch.setattr(CONTEXT, "github_document", github_document)
    monkeypatch.setattr(CONTEXT, "sleep", waits.append, raising=False)
    context = CONTEXT.collect_context({"workflow_run": run})
    assert context["artifacts"]["bats-junit"]["id"] == artifact["id"]
    assert len(waits) == 1
    assert calls[-1] == f"{route}/artifacts?per_page=100"


def test_persistent_stale_metadata_stops_before_artifacts_are_published(
    run, jobs, monkeypatch
):
    jobs[0]["steps"][0]["status"] = "pending"
    elapsed = [0]
    requests = []

    def github_document(endpoint):
        requests.append(endpoint)
        if endpoint.endswith("/attempts/2"):
            return run
        assert endpoint.endswith("/jobs?per_page=100")
        return {"total_count": 1, "jobs": jobs}

    def sleep(seconds):
        elapsed[0] += seconds

    monkeypatch.setattr(CONTEXT, "github_document", github_document)
    monkeypatch.setattr(CONTEXT, "monotonic", lambda: elapsed[0], raising=False)
    monkeypatch.setattr(CONTEXT, "sleep", sleep, raising=False)
    with pytest.raises(ValueError, match="step metadata"):
        CONTEXT.collect_context({"workflow_run": run})
    assert elapsed[0] == 600
    assert len(requests) <= 32
    assert not any("/artifacts" in endpoint for endpoint in requests)


def test_completed_failed_upload_is_diagnostic_evidence_without_retry(
    run, jobs, monkeypatch
):
    jobs[0]["steps"][0].update(status="completed", conclusion="failure")
    waits = []
    route = f"repos/{CONTEXT.REPOSITORY}/actions/runs/{run['id']}"
    documents = {
        f"{route}/attempts/2": run,
        f"{route}/attempts/2/jobs?per_page=100": {"total_count": 1, "jobs": jobs},
        f"{route}/artifacts?per_page=100": {"total_count": 0, "artifacts": []},
    }
    monkeypatch.setattr(CONTEXT, "github_document", documents.__getitem__)
    monkeypatch.setattr(CONTEXT, "sleep", waits.append, raising=False)
    context = CONTEXT.collect_context({"workflow_run": run})
    assert not waits
    assert context["artifacts"]["bats-junit"]["id"] is None
    assert (
        "successful unique artifact upload"
        in context["artifacts"]["bats-junit"]["reason"]
    )


@pytest.mark.parametrize(
    "route",
    [
        "--hostname=foreign.test",
        "https://foreign.test",
        "repos/foreign/repository/commits/main",
        "repos/Castrozan/.dotfiles/actions/runs/1/../../secrets",
    ],
)
def test_github_routes_are_confined_before_execution(route, monkeypatch):
    calls = []
    monkeypatch.setattr(
        CONTEXT.subprocess, "run", lambda *args, **kwargs: calls.append(args)
    )
    with pytest.raises(ValueError, match="approved"):
        CONTEXT.github_document(route)
    assert not calls
