import os
import pathlib
import shutil
import subprocess

import pytest


HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DISCOVERY_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "discovery.sh"
PYTEST_TIER_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "pytest.sh"

REQUIRED_EXTERNAL_COMMANDS_FOR_COLLECTION = ("find", "sort", "uname")

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)


def _resolve_modern_bash_absolute_path():
    candidate_paths = []
    located_on_path = shutil.which("bash")
    if located_on_path:
        candidate_paths.append(located_on_path)
    candidate_paths.extend(MODERN_BASH_CANDIDATE_PATHS)
    for candidate_path in candidate_paths:
        if not candidate_path or not os.path.exists(candidate_path):
            continue
        probe = subprocess.run(
            [candidate_path, "-c", "echo ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
        )
        major_version = probe.stdout.strip()
        if major_version.isdigit() and int(major_version) >= 4:
            return candidate_path
    pytest.skip("no bash >= 4 available to exercise the pytest tier library")


def _resolve_required_command_absolute_paths():
    resolved = {}
    for command_name in REQUIRED_EXTERNAL_COMMANDS_FOR_COLLECTION:
        located = shutil.which(command_name)
        if located is None:
            pytest.skip(
                f"required command {command_name} unavailable to build a pytest-absent PATH"
            )
        resolved[command_name] = located
    return resolved


def _build_isolated_bin_directory_without_pytest(bin_directory, resolved_commands):
    for command_name, absolute_path in resolved_commands.items():
        (bin_directory / command_name).symlink_to(absolute_path)


def _invoke_pytest_tier_with_pytest_absent(fake_repo_root, isolated_bin_directory):
    modern_bash = _resolve_modern_bash_absolute_path()
    shell_program = (
        f"source {DISCOVERY_LIBRARY}\n"
        f"source {PYTEST_TIER_LIBRARY}\n"
        "_run_pytest_tier unit quick\n"
    )
    return subprocess.run(
        [modern_bash, "-c", shell_program],
        env={"PATH": str(isolated_bin_directory), "REPO_DIR": str(fake_repo_root)},
        capture_output=True,
        text=True,
    )


def test_pytest_tier_fails_loudly_when_tests_exist_but_pytest_absent(tmp_path):
    resolved_commands = _resolve_required_command_absolute_paths()
    isolated_bin_directory = tmp_path / "bin"
    isolated_bin_directory.mkdir()
    _build_isolated_bin_directory_without_pytest(
        isolated_bin_directory, resolved_commands
    )

    fake_repo_root = tmp_path / "repo"
    collected_tier_directory = (
        fake_repo_root / "home" / "base" / "mod" / "__tests__" / "unit"
    )
    collected_tier_directory.mkdir(parents=True)
    (collected_tier_directory / "test_dummy.py").write_text(
        "def test_placeholder():\n    assert True\n"
    )

    completed = _invoke_pytest_tier_with_pytest_absent(
        fake_repo_root, isolated_bin_directory
    )

    assert completed.returncode == 1, (
        "The pytest tier must FAIL when test files were collected but pytest is "
        f"absent, otherwise the whole tier vanishes green. Got exit {completed.returncode}.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "refusing to skip silently" in completed.stderr, (
        "The failure must explain that pytest is missing while collected tests "
        f"exist.\nstderr: {completed.stderr}"
    )


def test_pytest_tier_skips_cleanly_when_no_tests_and_pytest_absent(tmp_path):
    resolved_commands = _resolve_required_command_absolute_paths()
    isolated_bin_directory = tmp_path / "bin"
    isolated_bin_directory.mkdir()
    _build_isolated_bin_directory_without_pytest(
        isolated_bin_directory, resolved_commands
    )

    fake_repo_root = tmp_path / "repo"
    fake_repo_root.mkdir()

    completed = _invoke_pytest_tier_with_pytest_absent(
        fake_repo_root, isolated_bin_directory
    )

    assert completed.returncode == 0, (
        "With zero collected test files the tier must skip cleanly even when "
        f"pytest is absent. Got exit {completed.returncode}.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
