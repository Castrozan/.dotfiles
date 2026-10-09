from dataclasses import replace
import json
from types import SimpleNamespace

import check
import findings
import pytest


def legacy_finding():
    return findings.Finding("qlty", "complexity", "source.py", 7, "complex", "known", 9)


def test_recorded_findings_can_shrink_but_cannot_grow_or_multiply():
    recorded = legacy_finding()
    baseline = findings.baseline_entries([recorded])
    assert findings.new_findings([replace(recorded, score=8)], baseline) == []
    assert findings.new_findings([replace(recorded, score=10)], baseline)
    assert len(findings.new_findings([recorded, recorded], baseline)) == 1


def test_stricter_ceiling_is_not_consumed_by_a_larger_finding():
    recorded = legacy_finding()
    smaller = replace(recorded, score=7)
    baseline = findings.baseline_entries([recorded, smaller])
    assert findings.new_findings([smaller, recorded], baseline) == []


def test_file_and_rule_identity_survive_line_movements():
    issue = {
        "tool": "ruff",
        "ruleKey": "F821",
        "message": "Undefined variable",
        "snippet": "return missing",
        "location": {"path": "source.py", "range": {"startLine": 3}},
    }
    before = findings.issue_finding(issue)
    issue["location"]["range"]["startLine"] = 10
    assert findings.issue_finding(issue).identity == before.identity
    issue["location"]["path"] = "other.py"
    assert findings.issue_finding(issue).identity != before.identity


def test_new_duplicate_location_cannot_reuse_an_old_exception():
    issue = {
        "tool": "qlty",
        "ruleKey": "identical-code",
        "message": "Duplicate code",
        "snippet": "existing block",
        "location": {"path": "source.py"},
        "otherLocations": [{"path": "old.py"}],
    }
    recorded = findings.issue_finding(issue)
    issue["otherLocations"].append({"path": "new.py"})
    assert findings.new_findings(
        [findings.issue_finding(issue)], findings.baseline_entries([recorded])
    )


def test_complexity_gate_only_checks_functions_above_five():
    statistics = [
        {
            "path": "source.py",
            "fullyQualifiedName": "small",
            "kind": "COMPONENT_TYPE_FUNCTION",
            "cyclomatic": 5,
        },
        {
            "path": "source.py",
            "fullyQualifiedName": "large",
            "kind": "COMPONENT_TYPE_FUNCTION",
            "cyclomatic": 6,
        },
        {
            "path": "directory",
            "fullyQualifiedName": "directory",
            "kind": "COMPONENT_TYPE_DIRECTORY",
            "cyclomatic": 500,
        },
    ]
    result = findings.collect_findings({"complexity": {"stats": statistics}})
    assert len(result) == 1
    assert result[0].score == 6
    assert "large" in result[0].message


def test_missing_metric_data_is_an_analysis_error(tmp_path):
    failures = []
    check.evaluate_reports(tmp_path, {"complexity": {}}, failures)
    assert failures


def test_baseline_cannot_absorb_a_new_finding_or_analysis_failure(tmp_path):
    directory = tmp_path / ".qlty"
    directory.mkdir()
    original = legacy_finding()
    path = directory / "baseline.json"
    path.write_text(json.dumps(findings.baseline_entries([original])))
    initial = path.read_text()
    introduced = replace(original, identity="new")
    assert check.update_baseline(tmp_path, [introduced], [introduced], []) == [
        introduced
    ]
    assert check.update_baseline(tmp_path, [original], [], ["scanner crashed"]) == []
    assert path.read_text() == initial


def test_baseline_can_remove_resolved_findings(tmp_path):
    directory = tmp_path / ".qlty"
    directory.mkdir()
    path = directory / "baseline.json"
    path.write_text(json.dumps(findings.baseline_entries([legacy_finding()])))
    assert check.update_baseline(tmp_path, [], [], []) == []
    assert json.loads(path.read_text()) == []


@pytest.mark.parametrize(
    "argv",
    [
        ["--all", "source.py"],
        ["--base", "main", "source.py"],
        ["--write-baseline", "source.py"],
    ],
)
def test_conflicting_or_partial_baseline_selections_fail(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["dotfiles-lint", *argv])
    with pytest.raises(SystemExit) as error:
        check.arguments()
    assert error.value.code == 2


def test_machine_report_does_not_expose_source_snippets():
    report = findings.report_data([legacy_finding()], [], [])
    assert report["passed"] is True
    assert "snippet" not in json.dumps(report)


@pytest.mark.parametrize("selected", ["../outside.py", "missing.py"])
def test_invalid_selected_paths_fail_before_analysis(tmp_path, selected):
    parsed = SimpleNamespace(paths=[selected], base=None)
    assert check.selection_failure(tmp_path, parsed)


def test_valid_paths_keep_the_option_separator(tmp_path):
    selected = "--all.py"
    (tmp_path / selected).write_text("")
    parsed = SimpleNamespace(paths=[selected], base=None)
    assert check.selection_failure(tmp_path, parsed) is None
    assert check.analysis_selection(parsed) == ["--", selected]


def test_invalid_base_is_rejected_by_git_without_an_option(monkeypatch, tmp_path):
    def reject(command, **keywords):
        assert command[-2:] == ["--end-of-options", "--bad^{commit}"]
        raise check.subprocess.CalledProcessError(128, command)

    monkeypatch.setattr(check.subprocess, "run", reject)
    parsed = SimpleNamespace(paths=[], base="--bad")
    assert check.selection_failure(tmp_path, parsed)


@pytest.mark.parametrize(
    "entry", [{"count": -1}, {"score": -1}, {"count": 1.5}, {"count": True}]
)
def test_malformed_baseline_counts_and_scores_fail(entry):
    baseline = {"identity": "known", "score": 9, "count": 1} | entry
    with pytest.raises(ValueError):
        findings.new_findings([legacy_finding()], [baseline])
