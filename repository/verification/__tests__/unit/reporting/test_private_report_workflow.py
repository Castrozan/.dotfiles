from pathlib import Path

import yaml

REPOSITORY = Path(__file__).resolve().parents[5]
WORKFLOW_PATH = REPOSITORY / ".github/workflows/publish-quality-overview.yml"
REPORT_ARTIFACT_BASE_URL = (
    "https://lucaszanoni.com/engineering/dotfiles/reports/data/reports/"
)


def report_job():
    return yaml.safe_load(WORKFLOW_PATH.read_text())["jobs"]["overview"]


def test_report_publication_has_no_retired_google_transport_or_identity_grant():
    source = WORKFLOW_PATH.read_text()
    for retired_transport in (
        "google-github-actions",
        "gcloud",
        "gs://",
        "storage.googleapis.com",
        "REPORT_BUCKET",
        "REPORTS_STATIC_GCS_PUBLISH",
    ):
        assert retired_transport not in source
    assert "id-token" not in report_job()["permissions"]
    caller = yaml.safe_load(
        (REPOSITORY / ".github/workflows/reports-deploy.yml").read_text()
    )
    assert "id-token" not in caller["jobs"]["quality-overview"]["permissions"]


def test_report_publication_uses_private_versioned_and_promoted_artifact_trees():
    job = report_job()
    assert job["env"]["REPORT_ARTIFACT_BASE_URL"] == REPORT_ARTIFACT_BASE_URL
    steps = job["steps"]
    publications = [
        step for step in steps if "publish_report_artifacts.py" in step.get("run", "")
    ]
    assert len(publications) == 2
    versioned, current = publications
    assert ".quality-results/overview/payload.json" in versioned["run"]
    assert ".quality-results/overview/site" in versioned["run"]
    assert "reports/overview/$SOURCE_RUN_ID/$SOURCE_RUN_ATTEMPT/" in versioned["run"]
    eligibility = next(
        step for step in steps if step.get("id") == "publication_eligibility"
    )
    assert "steps.overview.outcome == 'success'" in eligibility["if"]
    assert "steps.publication_eligibility.outputs.current == 'true'" in versioned["if"]
    assert steps.index(eligibility) < steps.index(versioned)
    assert ".quality-results/overview/payload.json" in current["run"]
    assert (
        "steps.current_publication_eligibility.outputs.current == 'true'"
        in current["if"]
    )
    assert "steps.reports.outcome == 'success'" in current["if"]
    for step in publications:
        for variable_name, configuration_context in (
            ("INGEST_BASE_URL", "vars"),
            ("INGEST_PRODUCER_SECRET", "secrets"),
        ):
            expected_expression = f"${{{{ {configuration_context}.{variable_name} }}}}"
            assert step["env"][variable_name] == expected_expression
    promotion = next(step for step in steps if step.get("id") == "promotion")
    assert "steps.overview_artifacts.outcome == 'success'" in promotion["if"]
    recheck = next(
        step for step in steps if step.get("id") == "current_publication_eligibility"
    )
    assert steps.index(versioned) < steps.index(recheck) < steps.index(current)
    assert steps.index(current) < steps.index(promotion)
    assert "steps.current_artifacts.outcome == 'success'" in promotion["if"]


def test_report_provenance_and_completeness_controls_remain_in_the_pipeline():
    steps = report_job()["steps"]
    source = WORKFLOW_PATH.read_text()
    for control in (
        "workflow_context.py",
        "download_artifacts.py",
        "promote_snapshot.py",
        "check_completeness.mjs",
        'agent-evals" testes',
    ):
        assert control in source
    assert any(
        step.get("with", {}).get("ref") == "${{ env.SOURCE_REVISION }}"
        for step in steps
    )
    assert "baseline --rodar" not in source
    coverage = next(
        step
        for step in steps
        if "publish_test_coverage_snapshot.py" in step.get("run", "")
    )
    assert "steps.current_artifacts.outcome == 'success'" in coverage["if"]


def test_manual_report_replay_is_main_only_and_uses_confirmed_source_environment():
    caller = yaml.safe_load(
        (REPOSITORY / ".github/workflows/reports-deploy.yml").read_text()
    )
    replay = caller[True]["workflow_dispatch"]["inputs"]["producing_run_id"]
    assert replay["required"] is True
    assert replay["type"] == "string"
    assert (
        "github.event_name == 'workflow_dispatch'"
        in caller["jobs"]["quality-overview"]["if"]
    )
    assert "github.ref == 'refs/heads/main'" in caller["jobs"]["quality-overview"]["if"]
    binding = next(
        step
        for step in report_job()["steps"]
        if "workflow_context.py" in step.get("run", "")
    )
    assert '--github-env "$GITHUB_ENV"' in binding["run"]
