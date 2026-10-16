import shutil
import sys
import xml.etree.ElementTree as ElementTree

import coverage
import pytest

import python_evidence_fixture


MERGER = python_evidence_fixture.MERGER
MODULE_PATH = python_evidence_fixture.MODULE_PATH


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    return python_evidence_fixture.create_evidence(tmp_path, monkeypatch)


def test_complete_native_suites_and_real_branch_coverage_are_combined(evidence):
    artifacts, output, _ = evidence
    native_suites = {}
    for tier, index, count in MERGER.EXPECTED_SHARDS:
        report = (
            artifacts
            / f"python-shard-{tier}-{index}-2/.quality-results/pytest-{tier}-shard-{index}-of-{count}.xml"
        )
        native_suites.setdefault(tier, []).append(
            ElementTree.tostring(python_evidence_fixture.read_xml(report)[0])
        )
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2)) == []
    for tier, expected in native_suites.items():
        report = python_evidence_fixture.read_xml(
            output / f".quality-results/pytest-{tier}.xml"
        )
        assert [ElementTree.tostring(suite) for suite in report] == expected
    combined = coverage.CoverageData(
        basename=str(output / ".coverage-reports/.coverage")
    )
    combined.read()
    assert set(combined.measured_files()) == {"repository/owned.py"}
    assert set(combined.lines("repository/owned.py")) == {1, 2, 4}
    assert set(combined.arcs("repository/owned.py")) == {
        (-1, 1),
        (1, 2),
        (1, 4),
        (2, -1),
        (4, -1),
    }
    report = python_evidence_fixture.read_xml(
        output / ".coverage-reports/python-coverage.xml"
    )
    assert report.get("lines-covered") == report.get("lines-valid") == "3"
    assert report.get("branches-covered") == report.get("branches-valid") == "2"


@pytest.mark.parametrize("missing", ["report", "coverage", "artifact"])
def test_missing_shard_preserves_available_diagnostics_without_false_complete_report(
    evidence, missing
):
    artifacts, output, _ = evidence
    shard = artifacts / "python-shard-integration-1-2"
    if missing == "artifact":
        shutil.rmtree(shard)
    elif missing == "report":
        (shard / ".quality-results/pytest-integration-shard-1-of-2.xml").unlink()
    else:
        (shard / ".coverage-reports/.coverage.integration-1").unlink()
    errors = MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert errors
    assert (output / ".quality-results/pytest-unit.xml").is_file()
    assert list((output / ".quality-results/shard-diagnostics").rglob("*.xml"))
    assert not (output / ".coverage-reports/python-coverage.xml").exists()
    if missing != "coverage":
        assert not (output / ".quality-results/pytest-integration.xml").exists()


@pytest.mark.parametrize(
    "content",
    ["<broken", "<foreign/>", "<testsuites/>", "<testsuite><testcase/></testsuite>"],
)
def test_malformed_native_report_is_retained_as_a_diagnostic_and_rejected(
    evidence, content
):
    artifacts, output, _ = evidence
    report = (
        artifacts
        / "python-shard-integration-1-2/.quality-results/pytest-integration-shard-1-of-2.xml"
    )
    report.write_text(content)
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert not (output / ".quality-results/pytest-integration.xml").exists()
    diagnostic = (
        output
        / ".quality-results/shard-diagnostics/python-shard-integration-1-2"
        / report.name
    )
    assert diagnostic.read_text() == content
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_case_collisions_across_shards_are_rejected(evidence):
    artifacts, output, _ = evidence
    report = (
        artifacts
        / "python-shard-integration-1-2/.quality-results/pytest-integration-shard-1-of-2.xml"
    )
    report.write_text(
        report.read_text().replace("owned.integration.1", "owned.integration.0")
    )
    assert any(
        "collision" in error
        for error in MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    )
    assert not (output / ".quality-results/pytest-integration.xml").exists()


@pytest.mark.parametrize(
    "name", ["python-shard-integration-1-2-copy", "python-shard-unit-0-1"]
)
def test_duplicate_or_stale_attempt_shard_is_rejected(evidence, name):
    artifacts, output, _ = evidence
    (artifacts / name).mkdir()
    assert any(
        "Unexpected" in error
        for error in MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    )
    assert not (output / ".quality-results/pytest-unit.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_corrupt_coverage_never_becomes_a_partial_complete_report(evidence):
    artifacts, output, _ = evidence
    (
        artifacts / "python-shard-unit-0-2/.coverage-reports/.coverage.unit-0"
    ).write_bytes(b"broken")
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_failed_retry_removes_stale_complete_outputs(evidence):
    artifacts, output, _ = evidence
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2)) == []
    shutil.rmtree(artifacts / "python-shard-integration-1-2")
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert not (output / ".quality-results/pytest-integration.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_cli_returns_failure_for_missing_inputs(evidence, monkeypatch, capsys):
    artifacts, output, _ = evidence
    shutil.rmtree(artifacts / "python-shard-unit-0-2")
    monkeypatch.setattr(
        sys, "argv", [str(MODULE_PATH), str(artifacts), str(output), "2", "2", "2"]
    )
    assert MERGER.main() == 1
    assert "Missing Python coverage shard" in capsys.readouterr().err


def test_mixed_producing_attempts_preserve_successful_shards_from_partial_reruns(
    evidence,
):
    artifacts, output, _ = evidence
    for tier, index in (("unit", 0), ("integration", 1)):
        (artifacts / f"python-shard-{tier}-{index}-2").rename(
            artifacts / f"python-shard-{tier}-{index}-1"
        )
    assert MERGER.merge_python_evidence(artifacts, output, (1, 2, 1)) == []
    assert (output / ".quality-results/pytest-unit.xml").is_file()
    assert (output / ".quality-results/pytest-integration.xml").is_file()
    assert (output / ".coverage-reports/python-coverage.xml").is_file()


@pytest.mark.parametrize("attempts", [(2, 2), (2, 0, 2)])
def test_incomplete_or_invalid_producing_attempts_cannot_create_outputs(
    evidence, attempts
):
    artifacts, output, _ = evidence
    with pytest.raises(ValueError, match="attempts"):
        MERGER.merge_python_evidence(artifacts, output, attempts)
    assert not output.exists()


@pytest.mark.parametrize("attempts", [(1, 2, 1), (2, 1, 2)])
def test_foreign_attempt_artifacts_cannot_substitute_for_exact_producing_attempts(
    evidence, attempts
):
    artifacts, output, _ = evidence
    errors = MERGER.merge_python_evidence(artifacts, output, attempts)
    assert any("Unexpected Python shard artifact" in error for error in errors)
    assert not (output / ".quality-results/pytest-unit.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()
