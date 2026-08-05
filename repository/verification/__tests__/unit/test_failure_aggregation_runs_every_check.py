import os
import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[2]
FAILURE_AGGREGATION_LIBRARY = HARNESS_TESTS_ROOT / "runner" / "failure-aggregation.sh"

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)

STUB_CHECKS = """
_run_first_failing_check() { echo "ran first"; return 1; }
_run_passing_check() { echo "ran passing"; return 0; }
_run_second_failing_check() { echo "ran second"; return 1; }
"""


def resolve_modern_bash_absolute_path() -> str:
    candidates = [shutil.which("bash"), *MODERN_BASH_CANDIDATE_PATHS]
    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        probe = subprocess.run(
            [candidate, "-c", "echo ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
        )
        if probe.stdout.strip().isdigit() and int(probe.stdout.strip()) >= 4:
            return candidate
    pytest.skip("no bash >= 4 available to exercise the aggregation library")


def aggregate_stub_checks(shell_options: str, check_names: str):
    return subprocess.run(
        [
            resolve_modern_bash_absolute_path(),
            "-c",
            f"{shell_options}\n"
            f"source {FAILURE_AGGREGATION_LIBRARY}\n"
            f"{STUB_CHECKS}\n"
            f"_run_checks_reporting_every_failure {check_names}\n",
        ],
        capture_output=True,
        text=True,
    )


class TestEveryCheckRuns:
    def test_a_failing_check_does_not_stop_the_ones_after_it(self):
        completed = aggregate_stub_checks(
            "set -Eeuo pipefail",
            "_run_first_failing_check _run_passing_check _run_second_failing_check",
        )

        assert "ran first" in completed.stdout
        assert "ran passing" in completed.stdout
        assert "ran second" in completed.stdout, (
            "a check after the first failure must still run, otherwise CI reports one "
            "error per push and the fix takes as many passes as there are failures.\n"
            f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
        )

    def test_the_summary_names_every_failed_check(self):
        completed = aggregate_stub_checks(
            "set -Eeuo pipefail",
            "_run_first_failing_check _run_passing_check _run_second_failing_check",
        )

        assert "FAILED: first_failing_check" in completed.stdout
        assert "FAILED: second_failing_check" in completed.stdout
        assert "2 of 3 checks failed" in completed.stdout

    def test_a_failed_run_exits_non_zero(self):
        completed = aggregate_stub_checks(
            "set -Eeuo pipefail", "_run_passing_check _run_first_failing_check"
        )

        assert completed.returncode != 0

    def test_an_all_green_run_exits_zero_and_prints_no_failure_summary(self):
        completed = aggregate_stub_checks("set -Eeuo pipefail", "_run_passing_check")

        assert completed.returncode == 0
        assert "FAILED" not in completed.stdout

    def test_it_aggregates_the_same_way_without_errexit(self):
        completed = aggregate_stub_checks(
            "", "_run_first_failing_check _run_second_failing_check"
        )

        assert completed.returncode != 0
        assert "ran second" in completed.stdout
