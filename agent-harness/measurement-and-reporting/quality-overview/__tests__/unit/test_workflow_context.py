import copy
import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "publishing/workflow_context.py"
SPECIFICATION = importlib.util.spec_from_file_location("workflow_context", MODULE_PATH)
CONTEXT = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(CONTEXT)


@pytest.fixture
def run():
    return {
        "id": 123,
        "run_attempt": 2,
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/tests.yml",
        "status": "completed",
        "conclusion": "failure",
        "head_sha": "a" * 40,
        "repository": {"full_name": CONTEXT.REPOSITORY},
        "head_repository": {"full_name": CONTEXT.REPOSITORY},
        "run_started_at": "2026-09-26T00:10:00Z",
        "updated_at": "2026-09-26T00:20:00Z",
    }


@pytest.fixture
def artifact(run):
    return {
        "id": 456,
        "name": "bats-junit",
        "expired": False,
        "created_at": "2026-09-26T00:12:00Z",
        "workflow_run": {"id": run["id"], "head_sha": run["head_sha"]},
    }


def test_failed_workflow_retains_available_evidence_and_missing_inventory(
    run, artifact
):
    context = CONTEXT.build_context(run, [], [artifact])
    assert context["workflow"]["conclusion"] == "failure"
    assert context["workflow"]["runAttempt"] == 2
    assert context["artifacts"]["bats-junit"] == {"id": 456, "reason": None}
    assert context["artifacts"]["python-junit"]["id"] is None
    assert "found 0" in context["artifacts"]["python-junit"]["reason"]


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
    run, artifact, changes
):
    artifact.update(changes)
    context = CONTEXT.build_context(run, [], [artifact])
    assert context["artifacts"]["bats-junit"]["id"] is None
    assert context["artifacts"]["bats-junit"]["reason"]


def test_duplicate_named_artifacts_are_ambiguous(run, artifact):
    duplicate = {**artifact, "id": 789}
    context = CONTEXT.build_context(run, [], [artifact, duplicate])
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


def test_promotion_rejects_newer_main_and_rerun_attempt(run, monkeypatch):
    monkeypatch.syspath_prepend(str(MODULE_PATH.parent))
    import promote_snapshot

    payload = {"workflow": CONTEXT.workflow_identity(run)}
    assert promote_snapshot.promotion_matches(payload, run["head_sha"], run, run)
    assert not promote_snapshot.promotion_matches(payload, "b" * 40, run, run)
    assert not promote_snapshot.promotion_matches(
        payload, run["head_sha"], {**run, "run_attempt": 3}, run
    )


def test_stored_receipt_must_match_the_expected_report_location(
    run, tmp_path, monkeypatch
):
    monkeypatch.syspath_prepend(str(MODULE_PATH.parent))
    import promote_snapshot

    expected = {"workflow": CONTEXT.workflow_identity(run)}
    foreign = {"workflow": CONTEXT.workflow_identity({**run, "id": 999})}
    monkeypatch.chdir(tmp_path)
    receipt_path = tmp_path / ".quality-results/overview/payload.json"
    context_path = tmp_path / ".quality-results/workflow-context.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(foreign))
    context_path.write_text(json.dumps(expected))
    monkeypatch.setattr(
        promote_snapshot,
        "github_document",
        lambda route: pytest.fail("Foreign receipt queried GitHub"),
    )
    with pytest.raises(ValueError, match="Stored receipt"):
        promote_snapshot.main()


@pytest.mark.parametrize("latest_attempt", [2, 3])
def test_promotion_uses_attempt_timestamp_and_rejects_newer_attempt(
    run, tmp_path, monkeypatch, capsys, latest_attempt
):
    monkeypatch.syspath_prepend(str(MODULE_PATH.parent))
    import promote_snapshot

    payload = {"workflow": CONTEXT.workflow_identity(run)}
    latest = {
        **run,
        "run_attempt": latest_attempt,
        "updated_at": "2026-09-26T00:19:59Z",
    }
    route = f"repos/{CONTEXT.REPOSITORY}"
    responses = {
        f"{route}/commits/main": {"sha": run["head_sha"]},
        f"{route}/actions/runs/123": latest,
        f"{route}/actions/runs/123/attempts/2": run,
    }
    monkeypatch.chdir(tmp_path)
    output = tmp_path / ".quality-results/overview"
    output.mkdir(parents=True)
    (output / "payload.json").write_text(json.dumps(payload))
    (output.parent / "workflow-context.json").write_text(json.dumps(payload))
    monkeypatch.setattr(promote_snapshot, "github_document", responses.__getitem__)
    promote_snapshot.main()
    assert capsys.readouterr().out.strip() == (
        "true" if latest_attempt == 2 else "false"
    )
