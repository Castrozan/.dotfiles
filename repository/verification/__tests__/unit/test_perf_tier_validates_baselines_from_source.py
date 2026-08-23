import json
import os
import pathlib
import shutil
import subprocess
from datetime import datetime, timezone

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = HARNESS_TESTS_ROOT.parents[1]
PERF_TIER_LIBRARY = HARNESS_TESTS_ROOT / "runner" / "perf.sh"

CAPABILITY_RELATIVE_PATH = pathlib.Path("machine-configuration/development/testing")
CAPABILITY_SOURCE_DIRECTORY = REPOSITORY_ROOT / CAPABILITY_RELATIVE_PATH

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)

BASELINE_FILE_NAME_PER_TIER_FUNCTION = {
    "_run_rebuild_baseline_check": "baseline.json",
    "_run_desktop_baseline_check": "baseline-desktop.json",
}

MEASUREMENT_PER_BASELINE_FILE_NAME = {
    "baseline.json": {"eval": {"duration_seconds": 2.0, "max_allowed_seconds": 3.0}},
    "baseline-desktop.json": {"tmux": {"avg_ms": 20.0, "max_allowed_ms": 40.0}},
}


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
    pytest.skip("no bash >= 4 available to exercise the perf tier library")


def _command_poor_bin_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    interpreter = shutil.which("python3")
    if interpreter is None:
        pytest.skip("python3 unavailable to run the baseline validators from source")
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    (bin_directory / "python3").symlink_to(interpreter)
    return bin_directory


def _tracked_baseline(file_name: str, **overrides) -> dict:
    baseline = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": "abc1234",
        "host": "kira",
        "config": "darwin",
        "threshold_percent": 150,
        "measurements": MEASUREMENT_PER_BASELINE_FILE_NAME[file_name],
    }
    baseline.update(overrides)
    return baseline


def _checkout_with_baseline(
    tmp_path: pathlib.Path, file_name: str, baseline: dict
) -> pathlib.Path:
    checkout_root = tmp_path / "checkout"
    capability_directory = checkout_root / CAPABILITY_RELATIVE_PATH
    capability_directory.mkdir(parents=True)
    (capability_directory / "scripts").symlink_to(
        CAPABILITY_SOURCE_DIRECTORY / "scripts"
    )
    (capability_directory / file_name).write_text(json.dumps(baseline))
    return checkout_root


def _run_tier_function(
    tier_function: str, checkout_root: pathlib.Path, bin_directory: pathlib.Path
):
    return subprocess.run(
        [
            _resolve_modern_bash_absolute_path(),
            "-c",
            f"source {PERF_TIER_LIBRARY}\n{tier_function}\n",
        ],
        env={
            "PATH": str(bin_directory),
            "HOME": str(checkout_root.parent),
            "REPO_DIR": str(checkout_root),
        },
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("tier_function", "baseline_file_name"),
    sorted(BASELINE_FILE_NAME_PER_TIER_FUNCTION.items()),
)
def test_the_check_validates_the_source_baseline_without_the_installed_command(
    tmp_path, tier_function, baseline_file_name
):
    bin_directory = _command_poor_bin_directory(tmp_path)
    checkout_root = _checkout_with_baseline(
        tmp_path, baseline_file_name, _tracked_baseline(baseline_file_name)
    )

    completed = _run_tier_function(tier_function, checkout_root, bin_directory)

    assert completed.returncode == 0, (
        f"{tier_function} must validate {baseline_file_name} straight from the "
        "repository sources, because continuous integration never has the packaged "
        f"benchmark command on PATH.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "SKIP" not in completed.stdout + completed.stderr, (
        "a skip here is the hole this check closes: the tier would report green "
        "without reading either baseline.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


@pytest.mark.parametrize(
    ("tier_function", "baseline_file_name"),
    sorted(BASELINE_FILE_NAME_PER_TIER_FUNCTION.items()),
)
def test_the_check_propagates_an_invalid_source_baseline_as_a_failure(
    tmp_path, tier_function, baseline_file_name
):
    bin_directory = _command_poor_bin_directory(tmp_path)
    unattributed_baseline = _tracked_baseline(baseline_file_name)
    del unattributed_baseline["host"]
    checkout_root = _checkout_with_baseline(
        tmp_path, baseline_file_name, unattributed_baseline
    )

    completed = _run_tier_function(tier_function, checkout_root, bin_directory)

    assert completed.returncode != 0, (
        f"{tier_function} must return the validator's exit code, otherwise the "
        "trailing echo becomes the function's status and an unusable baseline reads "
        "as a pass once the tier runner drops errexit.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "Baseline has no recorded host." in completed.stdout, (
        "the failure must name what is wrong with the tracked baseline.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
