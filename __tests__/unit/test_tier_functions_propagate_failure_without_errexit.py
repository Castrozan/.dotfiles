import os
import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DISCOVERY_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "discovery.sh"
PYTEST_TIER_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "pytest.sh"

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
