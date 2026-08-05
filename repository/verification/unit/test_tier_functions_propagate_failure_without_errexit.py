import os
import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DISCOVERY_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "discovery.sh"
PYTEST_TIER_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "pytest.sh"
LINE_COUNT_TIER_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "line-counts.sh"

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)


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
    pytest.skip("no bash >= 4 available to exercise the tier libraries")


def build_repo_with_one_failing_unit_test(repo_root: pathlib.Path) -> None:
    tier_directory = repo_root / "home" / "base" / "mod" / "__tests__" / "unit"
    tier_directory.mkdir(parents=True)
    (tier_directory / "test_failing.py").write_text(
        "def test_that_fails():\n    assert False\n"
    )


def run_pytest_tier_without_errexit(repo_root: pathlib.Path):
    return subprocess.run(
        [
            resolve_modern_bash_absolute_path(),
            "-c",
            f"source {DISCOVERY_LIBRARY}\n"
            f"source {PYTEST_TIER_LIBRARY}\n"
            "_run_pytest_tier unit quick\n",
        ],
        env={"PATH": os.environ["PATH"], "REPO_DIR": str(repo_root)},
        capture_output=True,
        text=True,
    )


def test_the_pytest_tier_reports_a_failing_run_without_relying_on_errexit(tmp_path):
    if shutil.which("pytest") is None:
        pytest.skip("pytest unavailable")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    build_repo_with_one_failing_unit_test(repo_root)

    completed = run_pytest_tier_without_errexit(repo_root)

    assert completed.returncode != 0, (
        "the tier function must return the runner's exit code, otherwise a caller "
        "without set -e, which is exactly how CI sources these libraries, records a "
        "green run over failing tests.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


def run_line_count_check_without_errexit(script_directory: pathlib.Path):
    return subprocess.run(
        [
            resolve_modern_bash_absolute_path(),
            "-c",
            f"SCRIPT_DIR={script_directory}\n"
            f"source {LINE_COUNT_TIER_LIBRARY}\n"
            "_run_line_count_check\n",
        ],
        capture_output=True,
        text=True,
    )


def test_the_line_count_check_reports_a_violation_without_relying_on_errexit(tmp_path):
    if shutil.which("python3") is None:
        pytest.skip("python3 unavailable")
    (tmp_path / "check-line-counts.py").write_text("raise SystemExit(1)\n")

    completed = run_line_count_check_without_errexit(tmp_path)

    assert completed.returncode != 0, (
        "the check must return the policy script's exit code, otherwise the trailing "
        "echo becomes the function's status and a violation reads as a pass once the "
        "tier runner drops errexit to aggregate failures.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


def test_the_line_count_check_still_reports_success_when_the_policy_holds(tmp_path):
    if shutil.which("python3") is None:
        pytest.skip("python3 unavailable")
    (tmp_path / "check-line-counts.py").write_text("raise SystemExit(0)\n")

    completed = run_line_count_check_without_errexit(tmp_path)

    assert completed.returncode == 0


def test_the_pytest_tier_still_reports_success_when_the_run_passes(tmp_path):
    if shutil.which("pytest") is None:
        pytest.skip("pytest unavailable")
    repo_root = tmp_path / "repo"
    tier_directory = repo_root / "home" / "base" / "mod" / "__tests__" / "unit"
    tier_directory.mkdir(parents=True)
    (tier_directory / "test_passing.py").write_text(
        "def test_that_passes():\n    assert True\n"
    )

    completed = run_pytest_tier_without_errexit(repo_root)

    assert completed.returncode == 0, (
        f"a passing tier must exit 0.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
