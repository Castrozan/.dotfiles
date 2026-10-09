import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from analyze import collect_analysis
from findings import baseline_entries, collect_findings, new_findings, report_data
from repository_checks import repository_failures


def arguments():
    parser = argparse.ArgumentParser(description="Run dotfiles quality checks locally")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--base", help="Analyze changes relative to a Git revision")
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--write-baseline", action="store_true")
    parsed = parser.parse_args()
    reject_mixed_paths(parser, parsed)
    reject_partial_baseline(parser, parsed)
    return parsed


def reject_mixed_paths(parser, parsed):
    if not parsed.paths:
        return
    if any((parsed.all, parsed.base)):
        parser.error("paths cannot be combined with --all or --base")


def reject_partial_baseline(parser, parsed):
    if not parsed.write_baseline:
        return
    if any((parsed.paths, parsed.base)):
        parser.error("--write-baseline requires a complete scan")


def analysis_selection(parsed):
    if parsed.paths:
        return ["--", *parsed.paths]
    if parsed.base:
        return ["--upstream", parsed.base]
    return ["--all"]


def validate_selected_path(repository, selected):
    path = (repository / selected).resolve()
    if not path.is_relative_to(repository):
        raise ValueError(f"Path is outside the repository: {selected}")
    if not path.exists():
        raise ValueError(f"Path does not exist: {selected}")


def selection_failure(repository, parsed):
    try:
        for selected in parsed.paths:
            validate_selected_path(repository, selected)
        if parsed.base:
            subprocess.run(
                [
                    "git",
                    "rev-parse",
                    "--verify",
                    "--end-of-options",
                    parsed.base + "^{commit}",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        return str(error)
    return None


def print_report(report, machine_readable):
    if machine_readable:
        print(json.dumps(report, indent=2))
        return
    for failure in report["errors"]:
        print(f"ERROR: {failure}", file=sys.stderr)
    for finding in report["newFindings"]:
        print(
            f"{finding['path']}:{finding['line']}: {finding['rule']}: {finding['message']}",
            file=sys.stderr,
        )
    print(
        f"Local lint: {len(report['newFindings'])} new findings, "
        f"{len(report['findings']) - len(report['newFindings'])} recorded findings, "
        f"{len(report['errors'])} errors"
    )


def evaluate_reports(repository, reports, failures):
    baseline_path = repository / ".qlty/baseline.json"
    findings = []
    try:
        findings = collect_findings(reports)
        baseline = (
            json.loads(baseline_path.read_text()) if baseline_path.exists() else []
        )
        violations = new_findings(findings, baseline)
    except (ValueError, KeyError, TypeError) as error:
        failures.append(f"Invalid analysis or baseline: {error}")
        violations = findings
    return findings, violations


def update_baseline(repository, findings, violations, failures):
    baseline_path = repository / ".qlty/baseline.json"
    if failures:
        return violations
    if baseline_path.exists() and violations:
        return violations
    baseline_path.write_text(json.dumps(baseline_entries(findings), indent=2) + "\n")
    return []


def emit_report(report, parsed):
    if parsed.output:
        parsed.output.parent.mkdir(parents=True, exist_ok=True)
        parsed.output.write_text(json.dumps(report, indent=2) + "\n")
    print_report(report, parsed.json)


def main():
    parsed = arguments()
    os.environ["QLTY_TELEMETRY"] = "off"
    os.environ["RAYON_NUM_THREADS"] = "2"
    repository = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    )
    failure = selection_failure(repository, parsed)
    if failure is not None:
        emit_report(report_data([], [], [failure]), parsed)
        return 1
    reports, failures = collect_analysis(repository, analysis_selection(parsed))
    findings, violations = evaluate_reports(repository, reports, failures)
    failures.extend(repository_failures(repository))
    if parsed.write_baseline:
        violations = update_baseline(repository, findings, violations, failures)
    report = report_data(findings, violations, failures)
    emit_report(report, parsed)
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
