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


def test_promotion_rejects_newer_main_and_rerun_attempt(run, monkeypatch):
    monkeypatch.syspath_prepend(str(MODULE_PATH.parent))
    import promote_snapshot

    payload = {"workflow": CONTEXT.workflow_identity(run)}
    assert promote_snapshot.promotion_matches(payload, run["head_sha"], run)
    assert not promote_snapshot.promotion_matches(payload, "b" * 40, run)
    assert not promote_snapshot.promotion_matches(
        payload, run["head_sha"], {**run, "run_attempt": 3}
    )


def test_stored_receipt_must_match_the_expected_report_location(
    run, tmp_path, monkeypatch
):
    monkeypatch.syspath_prepend(str(MODULE_PATH.parent))
    import promote_snapshot

    expected = {"workflow": CONTEXT.workflow_identity(run)}
    foreign = {"workflow": CONTEXT.workflow_identity({**run, "id": 999})}
    receipt_path = tmp_path / "payload.json"
    context_path = tmp_path / "context.json"
    receipt_path.write_text(json.dumps(foreign))
    context_path.write_text(json.dumps(expected))
    monkeypatch.setattr(
        promote_snapshot,
        "github_document",
        lambda route: pytest.fail("Foreign receipt queried GitHub"),
    )
    with pytest.raises(ValueError, match="Stored receipt"):
        promote_snapshot.main([str(receipt_path), str(context_path)])
