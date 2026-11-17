from pathlib import Path

import yaml


ROOT = next(
    parent for parent in Path(__file__).parents if (parent / ".github").is_dir()
)
WORKFLOW = ROOT / ".github/workflows/publish-quality-overview.yml"


def workflow_steps():
    document = yaml.safe_load(WORKFLOW.read_text())
    return document["jobs"]["overview"]["steps"]


def by_identifier(steps, identifier):
    return next(step for step in steps if step.get("id") == identifier)


def conjuncts(step):
    expression = step["if"].strip().removeprefix("${{").removesuffix("}}")
    assert "||" not in expression
    return {term.strip() for term in expression.split("&&")}


def test_stale_report_cannot_upload_before_generation_and_eligibility():
    steps = workflow_steps()
    versioned = by_identifier(steps, "overview_artifacts")
    reports = by_identifier(steps, "reports")
    assert steps.index(reports) < steps.index(versioned)
    eligibility = by_identifier(steps, "publication_eligibility")
    assert steps.index(reports) < steps.index(eligibility) < steps.index(versioned)
    assert "steps.publication_eligibility.outputs.current == 'true'" in conjuncts(
        versioned
    )
    assert "steps.overview_artifacts.outcome == 'success'" not in conjuncts(eligibility)
    assert "steps.reports.outcome == 'success'" in conjuncts(eligibility)


def test_all_file_uploads_require_eligibility_and_not_cancelled():
    steps = workflow_steps()
    uploads = [
        step for step in steps if "publish_report_artifacts.py" in step.get("run", "")
    ]
    assert len(uploads) == 2
    for step in uploads:
        terms = conjuncts(step)
        assert "steps.publication_eligibility.outputs.current == 'true'" in terms
        assert "!cancelled()" in terms


def test_current_artifacts_require_successful_versioned_publication():
    steps = workflow_steps()
    current = by_identifier(steps, "current_artifacts")
    assert "steps.overview_artifacts.outcome == 'success'" in conjuncts(current)
    assert "steps.reports.outcome == 'success'" in conjuncts(current)
    assert (
        "steps.current_publication_eligibility.outputs.current == 'true'"
        in conjuncts(current)
    )
    recheck = by_identifier(steps, "current_publication_eligibility")
    versioned = by_identifier(steps, "overview_artifacts")
    assert steps.index(versioned) < steps.index(recheck) < steps.index(current)


def test_final_freshness_is_rechecked_after_all_files_before_pointer_publication():
    steps = workflow_steps()
    current = by_identifier(steps, "current_artifacts")
    promotion = by_identifier(steps, "promotion")
    assert steps.index(current) < steps.index(promotion)
    assert "steps.overview_artifacts.outcome == 'success'" in conjuncts(promotion)
    assert "steps.current_artifacts.outcome == 'success'" in conjuncts(promotion)
    snapshots = [
        step
        for step in steps
        if "publish_quality_overview_snapshot.py" in step.get("run", "")
        or "publish_test_coverage_snapshot.py" in step.get("run", "")
    ]
    assert len(snapshots) == 2
    for step in snapshots:
        assert steps.index(promotion) < steps.index(step)
        assert "steps.promotion.outputs.current == 'true'" in conjuncts(step)
        assert "steps.overview_artifacts.outcome == 'success'" in conjuncts(step)
        assert "steps.current_artifacts.outcome == 'success'" in conjuncts(step)


def test_original_evidence_is_retained_before_any_remote_upload():
    steps = workflow_steps()
    first_upload = steps.index(by_identifier(steps, "overview_artifacts"))
    retained = [
        step
        for step in steps[:first_upload]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert any(
        step.get("with", {}).get("name") == "dotfiles-quality-overview"
        for step in retained
    )
    assert any(
        step.get("with", {}).get("name") == "dotfiles-current-reports"
        for step in retained
    )
    current_archive = by_identifier(steps, "current_reports_archive")
    assert "steps.reports.outcome == 'success'" in conjuncts(current_archive)
    eligibility = by_identifier(steps, "publication_eligibility")
    assert "steps.overview_archive.outcome == 'success'" in conjuncts(eligibility)
    assert "steps.current_reports_archive.outcome == 'success'" in conjuncts(
        eligibility
    )
