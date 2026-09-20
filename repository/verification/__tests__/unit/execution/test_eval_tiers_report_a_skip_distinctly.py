import os
import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[3]
EVALS_TIER_LIBRARY = HARNESS_TESTS_ROOT / "runner" / "evals.sh"

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)

SKIPPED_STATUS = 77

TIER_FUNCTIONS = ("_run_evals_tier", "_run_integration_tier", "_run_e2e_tier")


def _resolve_modern_bash_absolute_path() -> str:
    for candidate in [shutil.which("bash"), *MODERN_BASH_CANDIDATE_PATHS]:
        if not candidate or not os.path.exists(candidate):
            continue
        probe = subprocess.run(
            [candidate, "-c", "echo ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
        )
        if probe.stdout.strip().isdigit() and int(probe.stdout.strip()) >= 4:
            return candidate
    pytest.skip("no bash >= 4 available to exercise the evals tier library")


def _run_tier_without_its_tools(tier_function: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            _resolve_modern_bash_absolute_path(),
            "-c",
            f'source "{EVALS_TIER_LIBRARY}"; {tier_function}',
        ],
        env={"PATH": "", "REPO_DIR": str(HARNESS_TESTS_ROOT.parents[1])},
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_a_missing_tool_reports_a_skip_instead_of_a_pass(tier_function):
    completed = _run_tier_without_its_tools(tier_function)

    assert completed.returncode == SKIPPED_STATUS
    assert completed.returncode != 0, (
        f"{tier_function} returned success on a machine that cannot run it"
    )


@pytest.mark.parametrize("tier_function", TIER_FUNCTIONS)
def test_a_skip_says_which_tool_is_missing(tier_function):
    completed = _run_tier_without_its_tools(tier_function)

    assert "SKIP:" in completed.stderr
    assert "not installed" in completed.stderr
