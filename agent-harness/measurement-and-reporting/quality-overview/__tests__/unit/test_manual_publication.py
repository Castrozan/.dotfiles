import copy
import re

import pytest
from hypothesis import given, strategies as st

import workflow_context as CONTEXT


def test_manual_publication_uses_retained_actual_producing_run(
    monkeypatch, run, jobs, artifact
):
    responses = {
        f"repos/{CONTEXT.REPOSITORY}/actions/runs/123": run,
        f"repos/{CONTEXT.REPOSITORY}/actions/runs/123/attempts/2": run,
        f"repos/{CONTEXT.REPOSITORY}/actions/runs/123/attempts/2/jobs?per_page=100": {
            "jobs": jobs,
            "total_count": len(jobs),
        },
        f"repos/{CONTEXT.REPOSITORY}/actions/runs/123/artifacts?per_page=100": {
            "artifacts": [artifact],
            "total_count": 1,
        },
    }
    requested = []

    def read_metadata(route):
        requested.append(route)
        return responses[route]

    monkeypatch.setattr(CONTEXT, "github_document", read_metadata)
    context = CONTEXT.collect_context({"inputs": {"producing_run_id": "123"}})
    assert context["workflow"] == CONTEXT.workflow_identity(run)
    assert context["workflow"]["conclusion"] == "failure"
    assert context["artifacts"]["bats-junit"]["id"] == artifact["id"]
    assert requested[0] == f"repos/{CONTEXT.REPOSITORY}/actions/runs/123"


@given(st.text().filter(lambda value: re.fullmatch(r"[1-9][0-9]*", value) is None))
def test_invalid_manual_identifiers_refuse_before_metadata_lookup(value):
    requested = []
    original = CONTEXT.github_document
    CONTEXT.github_document = lambda route: requested.append(route)
    try:
        with pytest.raises(ValueError):
            CONTEXT.collect_context({"inputs": {"producing_run_id": value}})
    finally:
        CONTEXT.github_document = original
    assert requested == []


@pytest.mark.parametrize(
    "changes",
    [
        {"event": "pull_request"},
        {"head_branch": "other"},
        {"path": ".github/workflows/other.yml"},
        {"status": "in_progress"},
    ],
)
def test_manual_publication_keeps_producer_validation(monkeypatch, run, changes):
    invalid = {**copy.deepcopy(run), **changes}
    monkeypatch.setattr(CONTEXT, "github_document", lambda route: invalid)
    with pytest.raises(ValueError, match="completed main-push tests"):
        CONTEXT.collect_context({"inputs": {"producing_run_id": "123"}})


def test_confirmed_producing_environment_is_appended_without_rewriting_existing_values(
    tmp_path, run
):
    target = tmp_path / "github-env"
    target.write_text("EXISTING=value\n")
    CONTEXT.write_producing_environment(CONTEXT.workflow_identity(run), target)
    assert target.read_text() == (
        "EXISTING=value\nSOURCE_RUN_ID=123\nSOURCE_RUN_ATTEMPT=2\n"
        f"SOURCE_REVISION={run['head_sha']}\n"
    )


def test_manual_run_cannot_be_rebound_to_another_identifier(monkeypatch, run):
    monkeypatch.setattr(CONTEXT, "github_document", lambda route: {**run, "id": 456})
    with pytest.raises(ValueError, match="differs from returned metadata"):
        CONTEXT.collect_context({"inputs": {"producing_run_id": "123"}})
