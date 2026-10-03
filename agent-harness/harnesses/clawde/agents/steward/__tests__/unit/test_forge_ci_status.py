import json
from pathlib import Path

import pytest

from continuous_integration_status import continuous_integration_status_for_revision

REVISION = "b" * 40


def report(runs, code=0):
    def command(arguments, directory, timeout):
        assert arguments == ["git-forge", "--commit", REVISION]
        assert directory == Path("/repository")
        assert timeout == 45
        return code, json.dumps(runs)

    return continuous_integration_status_for_revision(
        Path("/repository"), REVISION, command
    )


def run(
    state="completed", conclusion="success", workflow="pipeline", revision=REVISION
):
    return {
        "headSha": revision,
        "status": state,
        "conclusion": conclusion,
        "workflowName": workflow,
        "url": "https://forge.example/run/1",
    }


def test_missing_pipeline_and_other_revisions_are_pending():
    assert report([])["state"] == "pending"
    assert report([run(revision="c" * 40)])["state"] == "pending"


@pytest.mark.parametrize("code", [1, 2, 127])
def test_inaccessible_provider_never_reports_clean(code):
    result = report([], code)
    assert result["state"] == "pending"
    assert result["query_error"]


@pytest.mark.parametrize(
    "conclusion", ["failed", "canceled", "cancelled", "skipped", "neutral"]
)
def test_every_non_success_terminal_verdict_is_failing(conclusion):
    assert report([run(conclusion=conclusion)])["state"] == "failing"


def test_latest_attempt_per_workflow_decides_the_verdict():
    result = report([run(), run(conclusion="failed")])
    assert result["state"] == "passing"
    assert result["workflows_checked"] == 1


def test_failure_wins_over_another_pending_workflow():
    result = report([run(conclusion="failed"), run("in_progress", None, "other")])
    assert result["state"] == "failing"
    assert result["pending"] == ["other"]
    assert result["failing"] == [
        {"workflow": "pipeline", "url": "https://forge.example/run/1"}
    ]


@pytest.mark.parametrize(
    "payload", ["invalid JSON", "{}", '[{"headSha":"' + REVISION + '"}]']
)
def test_malformed_metadata_is_pending(payload):
    result = continuous_integration_status_for_revision(
        Path("/repository"), REVISION, lambda *args: (0, payload)
    )
    assert result["state"] == "pending"
    assert result["parse_error"]
