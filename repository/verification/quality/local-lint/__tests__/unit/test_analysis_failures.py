import subprocess
import sys

import analyze
import check
import pytest
import repository_checks


def test_all_analyzers_run_after_a_crash_and_invalid_json(monkeypatch, tmp_path):
    invoked = []

    def run_analysis(command, repository):
        invoked.append(command)
        assert repository == tmp_path
        if "check" in command:
            raise RuntimeError("linter crashed")
        if "smells" in command:
            raise ValueError("invalid JSON")
        return {"stats": []}

    monkeypatch.setattr(analyze, "run_analysis", run_analysis)
    reports, failures = analyze.collect_analysis(tmp_path, ["--upstream", "main"])
    assert reports == {"complexity": {"stats": []}}
    assert len(failures) == 2
    assert len(invoked) == 3
    assert all(command[-2:] == ["--upstream", "main"] for command in invoked)
    assert "--no-fix" in invoked[0]


def test_missing_executable_is_a_failure(monkeypatch, tmp_path):
    def missing(command, repository):
        raise FileNotFoundError("qlty")

    monkeypatch.setattr(analyze, "run_analysis", missing)
    reports, failures = analyze.collect_analysis(tmp_path, ["--all"])
    assert reports == {}
    assert len(failures) == 3


def test_repository_checks_report_all_failures_after_a_timeout(monkeypatch, tmp_path):
    calls = []

    def run(command, **keywords):
        calls.append(command)
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(command, 60)
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="16 entries")

    monkeypatch.setattr(repository_checks.subprocess, "run", run)
    assert len(repository_checks.repository_failures(tmp_path)) == 3
    assert len(calls) == 3
    assert "--skip-snapshot-tests" in calls[-1]


def test_malformed_findings_cannot_pass_or_replace_baseline(tmp_path):
    failures = []
    findings, violations = check.evaluate_reports(
        tmp_path, {"lint": [{"tool": "ruff"}]}, failures
    )
    assert findings == []
    assert violations == []
    assert failures


@pytest.mark.parametrize(
    "program, expected_error",
    [("raise SystemExit(3)", RuntimeError), ("print('incomplete JSON')", ValueError)],
)
def test_real_process_failures_are_not_clean_reports(tmp_path, program, expected_error):
    with pytest.raises(expected_error):
        analyze.run_analysis([sys.executable, "-c", program], tmp_path)


def test_real_process_json_is_read_without_shell_evaluation(tmp_path):
    assert analyze.run_analysis([sys.executable, "-c", "print('[]')"], tmp_path) == []
