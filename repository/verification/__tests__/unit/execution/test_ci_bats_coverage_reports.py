import json
import os
from pathlib import Path
import shutil
import subprocess

from defusedxml import ElementTree
import pytest

VERIFICATION_ROOT = Path(__file__).resolve().parents[3]
RUNNER_FILES = (
    "bats.sh",
    "discovery.sh",
    "failure-aggregation.sh",
    "foreign-platform-test-roots.sh",
    "darwin-only-test-roots.txt",
    "linux-only-test-roots.txt",
)


@pytest.fixture
def owned_repository(tmp_path):
    for command in ("bash", "bats", "kcov", "bc"):
        if shutil.which(command) is None:
            pytest.skip(f"{command} is unavailable")
    repository = tmp_path / "owned repository"
    verification = repository / "repository/verification"
    (verification / "runner").mkdir(parents=True)
    (verification / "cover").mkdir()
    for filename in RUNNER_FILES:
        shutil.copy2(
            VERIFICATION_ROOT / "runner" / filename,
            verification / "runner" / filename,
        )
    shutil.copy2(
        VERIFICATION_ROOT / "cover/bash-coverage.sh",
        verification / "cover/bash-coverage.sh",
    )
    write_owned_bats_corpus(repository)
    return repository


def write_owned_bats_corpus(repository):
    source_directory = repository / "machine-configuration/fixture/scripts"
    outside_directory = repository / "agent-harness/fixture/scripts"
    unit_directory = repository / "machine-configuration/fixture/__tests__/unit"
    outside_tests = repository / "agent-harness/fixture/__tests__/unit"
    integration = repository / "machine-configuration/fixture/__tests__/integration"
    for directory in (
        source_directory,
        outside_directory,
        unit_directory,
        outside_tests,
        integration,
    ):
        directory.mkdir(parents=True)
    (source_directory / "inside-coverage.sh").write_text("measured_value=inside\n")
    (outside_directory / "outside-coverage.sh").write_text("measured_value=outside\n")
    (outside_tests / "outside.bats").write_text(
        '@test "outside pass" {\n'
        '  source "$REPO_DIR/agent-harness/fixture/scripts/outside-coverage.sh"\n'
        '  test "$measured_value" = outside\n'
        "}\n"
    )
    (unit_directory / "outcomes.bats").write_text(
        '@test "pass" {\n'
        '  source "$REPO_DIR/machine-configuration/fixture/scripts/inside-coverage.sh"\n'
        '  test "$measured_value" = inside\n'
        '  test -z "$DOTFILES_TEST_REPORT_DIRECTORY"\n'
        "}\n"
        '@test "conditional failure" { test "$OWNED_BATS_FAIL" = no; }\n'
        '@test "skip" { skip "owned unexecuted case"; }\n'
    )
    (integration / "pass.bats").write_text(
        '@test "integration pass" { test -z "$DOTFILES_TEST_REPORT_DIRECTORY"; }\n'
    )


def execute_owned_tier(repository, reports, fail, invocation):
    verification = repository / "repository/verification"
    shell = (
        "set -Eeuo pipefail\n"
        'source "$SCRIPT_DIR/runner/discovery.sh"\n'
        'source "$SCRIPT_DIR/runner/bats.sh"\n'
        'source "$SCRIPT_DIR/runner/failure-aggregation.sh"\n'
    )
    return subprocess.run(
        [shutil.which("bash"), "-c", shell + invocation],
        env={
            "PATH": os.environ["PATH"],
            "REPO_DIR": str(repository),
            "SCRIPT_DIR": str(verification),
            "DOTFILES_TEST_REPORT_DIRECTORY": str(reports),
            "OWNED_BATS_FAIL": "yes" if fail else "no",
        },
        capture_output=True,
        text=True,
        timeout=120,
    )


def native_cases(report_directory, tier):
    report = report_directory / f"bats-{tier}/report.xml"
    return ElementTree.parse(report).findall(".//testcase")


def assert_coverage_outputs(repository):
    directory = repository / "repository/verification/coverage/bats"
    coverage = json.loads((directory / "coverage.json").read_text())
    filenames = {entry["file"] for entry in coverage["files"]}
    assert any(name.endswith("inside-coverage.sh") for name in filenames)
    assert not any(name.endswith("outside-coverage.sh") for name in filenames)
    assert ElementTree.parse(directory / "cobertura.xml").getroot().tag == "coverage"


@pytest.mark.parametrize("fail", [False, True])
def test_ci_reuses_instrumented_unit_results_and_preserves_failures(
    owned_repository, tmp_path, fail
):
    plain_reports = tmp_path / "plain reports"
    plain = execute_owned_tier(
        owned_repository, plain_reports, fail, "_run_bats_tier unit quick\n"
    )
    reports = tmp_path / "instrumented reports"
    instrumented = execute_owned_tier(
        owned_repository,
        reports,
        fail,
        "_run_checks_reporting_every_failure "
        "_run_quick_bats_tests_ci _run_integration_scripts_bats_tests\n",
    )
    assert plain.returncode == instrumented.returncode == int(fail), (
        instrumented.stdout + instrumented.stderr
    )
    unit = native_cases(reports, "unit")
    original = native_cases(plain_reports, "unit")
    assert [(case.get("classname"), case.get("name")) for case in unit] == [
        (case.get("classname"), case.get("name")) for case in original
    ]
    assert len(unit) == 4
    assert sum(case.find("failure") is not None for case in unit) == int(fail)
    assert sum(case.find("skipped") is not None for case in unit) == 1
    assert len(native_cases(reports, "integration")) == 1
    assert "=== Coverage Summary ===" in instrumented.stdout
    assert "=== Per-file Coverage ===" in instrumented.stdout
    assert_coverage_outputs(owned_repository)
