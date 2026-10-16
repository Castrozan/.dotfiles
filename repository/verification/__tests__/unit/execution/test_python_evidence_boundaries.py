from copy import deepcopy
import xml.etree.ElementTree as ElementTree

import coverage
import pytest

import python_evidence_fixture


MERGER = python_evidence_fixture.MERGER


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    return python_evidence_fixture.create_evidence(tmp_path, monkeypatch)


def test_native_call_failure_and_teardown_error_keep_duplicate_case_identity(evidence):
    artifacts, output, _ = evidence
    report = (
        artifacts
        / "python-shard-unit-0-2/.quality-results/pytest-unit-shard-0-of-1.xml"
    )
    root = python_evidence_fixture.read_xml(report)
    suite = root[0]
    case = deepcopy(suite.find("testcase[@name='failure']"))
    case.remove(case.find("failure"))
    ElementTree.SubElement(case, "error", message="native teardown error")
    suite.append(case)
    suite.set("errors", "1")
    ElementTree.ElementTree(root).write(report)
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2)) == []
    result = python_evidence_fixture.read_xml(
        output / ".quality-results/pytest-unit.xml"
    )
    assert ElementTree.tostring(result[0]) == ElementTree.tostring(suite)
    assert len(result.findall(".//testcase[@name='failure']")) == 2


def test_foreign_report_cannot_impersonate_an_additional_native_shard(evidence):
    artifacts, output, _ = evidence
    report_directory = artifacts / "python-shard-integration-0-2/.quality-results"
    (report_directory / "pytest-integration-shard-0-of-2-copy.xml").write_text(
        "<testsuites/>"
    )
    assert any(
        "Duplicate" in error
        for error in MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    )
    assert not (output / ".quality-results/pytest-integration.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_dtd_and_entity_expansion_are_rejected(evidence):
    artifacts, output, _ = evidence
    report = (
        artifacts
        / "python-shard-unit-0-2/.quality-results/pytest-unit-shard-0-of-1.xml"
    )
    report.write_text(
        '<!DOCTYPE testsuites [<!ENTITY text "unsafe">]><testsuites>&text;</testsuites>'
    )
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert not (output / ".quality-results/pytest-unit.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_mixed_line_and_branch_data_are_rejected(evidence):
    artifacts, output, _ = evidence
    path = artifacts / "python-shard-unit-0-2/.coverage-reports/.coverage.unit-0"
    path.unlink()
    measurement = coverage.CoverageData(basename=str(path))
    measurement.add_lines({"repository/owned.py": {1}})
    measurement.write()
    assert any(
        "incompatible branch" in error
        for error in MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    )
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


def test_line_only_data_preserves_the_union_without_inventing_branches(evidence):
    artifacts, output, _ = evidence
    for tier, index, _ in MERGER.EXPECTED_SHARDS:
        path = (
            artifacts
            / f"python-shard-{tier}-{index}-2/.coverage-reports/.coverage.{tier}-{index}"
        )
        measurement = coverage.CoverageData(basename=str(path))
        measurement.read()
        lines = measurement.lines("repository/owned.py")
        path.unlink()
        measurement = coverage.CoverageData(basename=str(path))
        measurement.add_lines({"repository/owned.py": lines})
        measurement.write()
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2)) == []
    combined = coverage.CoverageData(
        basename=str(output / ".coverage-reports/.coverage")
    )
    combined.read()
    assert not combined.has_arcs()
    assert set(combined.lines("repository/owned.py")) == {1, 2, 4}
    report = python_evidence_fixture.read_xml(
        output / ".coverage-reports/python-coverage.xml"
    )
    assert report.get("branches-valid") == "0"


def test_report_generation_failure_cannot_leave_a_complete_looking_xml(evidence):
    artifacts, output, source = evidence
    source.unlink()
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    assert not (output / ".coverage-reports/python-coverage.xml").exists()


@pytest.mark.parametrize("outcome", ["failure", "error", "skipped"])
@pytest.mark.parametrize("name", [None, ""])
def test_unnamed_native_outcomes_survive_without_cross_shard_collisions(
    evidence, outcome, name
):
    artifacts, output, _ = evidence
    for tier, index, count in MERGER.EXPECTED_SHARDS:
        report = (
            artifacts
            / f"python-shard-{tier}-{index}-2/.quality-results/pytest-{tier}-shard-{index}-of-{count}.xml"
        )
        root = python_evidence_fixture.read_xml(report)
        case = root[0].find("testcase")
        case.attrib.pop("name")
        case.attrib.pop("classname")
        if name is not None:
            case.set("name", name)
        ElementTree.SubElement(
            case, outcome, message="native collection outcome"
        ).text = "owned diagnostics"
        ElementTree.ElementTree(root).write(report)
    assert MERGER.merge_python_evidence(artifacts, output, (2, 2, 2)) == []
    for tier, expected_count in (("unit", 1), ("integration", 2)):
        root = python_evidence_fixture.read_xml(
            output / f".quality-results/pytest-{tier}.xml"
        )
        unnamed = [case for case in root.iter("testcase") if not case.get("name")]
        assert len(unnamed) == expected_count
        assert all(case.find(outcome).text == "owned diagnostics" for case in unnamed)


@pytest.mark.parametrize("name", [None, ""])
def test_unnamed_case_without_native_outcome_is_malformed(evidence, name):
    artifacts, output, _ = evidence
    report = (
        artifacts
        / "python-shard-unit-0-2/.quality-results/pytest-unit-shard-0-of-1.xml"
    )
    root = python_evidence_fixture.read_xml(report)
    case = root[0].find("testcase")
    case.attrib.pop("name")
    if name is not None:
        case.set("name", name)
    ElementTree.ElementTree(root).write(report)
    assert any(
        "no outcome" in error
        for error in MERGER.merge_python_evidence(artifacts, output, (2, 2, 2))
    )
    assert not (output / ".quality-results/pytest-unit.xml").exists()
    assert not (output / ".coverage-reports/python-coverage.xml").exists()
