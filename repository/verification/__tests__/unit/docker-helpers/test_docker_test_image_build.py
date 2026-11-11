import os
import pathlib
import shutil
import subprocess

import pytest

VERIFICATION_ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCKER_ASSERTIONS_HELPER = (
    VERIFICATION_ROOT / "helpers" / "docker-container-assertions.bash"
)

MODERN_BASH_CANDIDATE_PATHS = (
    "/run/current-system/sw/bin/bash",
    f"/etc/profiles/per-user/{os.environ.get('USER', '')}/bin/bash",
    "/opt/homebrew/bin/bash",
)

SUBPROCESS_TIMEOUT_SECONDS = 30


def _resolve_modern_bash_absolute_path() -> str:
    for candidate in [shutil.which("bash"), *MODERN_BASH_CANDIDATE_PATHS]:
        if not candidate or not os.path.exists(candidate):
            continue
        probe = subprocess.run(
            [candidate, "-c", "echo ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
        if probe.stdout.strip().isdigit() and int(probe.stdout.strip()) >= 4:
            return candidate
    pytest.skip("no bash >= 4 available to exercise the docker assertions helper")


def _build_test_image_with_recording_docker(
    tmp_path: pathlib.Path, docker_exit_status: int
) -> tuple[subprocess.CompletedProcess, list[str]]:
    tool_directory = tmp_path / "bin"
    tool_directory.mkdir()
    recorded_arguments = tmp_path / "recorded-arguments"
    fake_docker = tool_directory / "docker"
    fake_docker.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$@" > "{recorded_arguments}"\n'
        f"exit {docker_exit_status}\n"
    )
    fake_docker.chmod(0o755)
    completed = subprocess.run(
        [
            _resolve_modern_bash_absolute_path(),
            "-c",
            f'source "{DOCKER_ASSERTIONS_HELPER}"; '
            "build_privileged_test_image_or_fail example-image",
        ],
        env={"PATH": f"{tool_directory}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    return completed, recorded_arguments.read_text().splitlines()


def test_the_test_image_build_resolves_names_through_the_host_network(tmp_path):
    completed, arguments = _build_test_image_with_recording_docker(tmp_path, 0)

    assert completed.returncode == 0, completed.stderr
    assert arguments[0] == "build"
    assert arguments[arguments.index("--network") + 1] == "host"


def test_the_test_image_build_still_tags_the_requested_image(tmp_path):
    _, arguments = _build_test_image_with_recording_docker(tmp_path, 0)

    assert arguments[arguments.index("-t") + 1] == "example-image"
    assert arguments[arguments.index("-f") + 1].endswith(
        "repository/verification/Dockerfile"
    )


def test_a_failed_image_build_fails_the_helper_and_reports_the_output(tmp_path):
    completed, _ = _build_test_image_with_recording_docker(tmp_path, 1)

    assert completed.returncode == 1
    assert "docker build failed for example-image" in completed.stderr
