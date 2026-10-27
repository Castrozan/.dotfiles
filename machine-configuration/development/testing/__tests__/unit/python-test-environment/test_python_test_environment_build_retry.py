import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

REPOSITORY = Path(__file__).resolve().parents[6]


def shard_workflow_steps():
    workflow = yaml.safe_load(
        (REPOSITORY / ".github/workflows/python-test-shard.yml").read_text()
    )
    return workflow["jobs"]["python"]["steps"], workflow["jobs"]["python"]["env"]


def run_environment_build_step(tmp_path, successful_attempt):
    steps, environment = shard_workflow_steps()
    script = next(
        step["run"]
        for step in steps
        if step.get("name", "").startswith("Build the Python test environment")
    )
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    attempts = tmp_path / "attempts"
    fake_nix = executable_directory / "nix"
    fake_nix.write_text(
        "#!/usr/bin/env bash\n"
        f'echo attempt >> "{attempts}"\n'
        f'[ "$(wc -l < "{attempts}")" -ge {successful_attempt} ]\n'
    )
    fake_nix.chmod(0o755)
    process = subprocess.run(
        [shutil.which("bash"), "-e", "-c", script],
        env=dict(
            os.environ,
            PATH=f"{executable_directory}:{os.environ['PATH']}",
            TEST_ENVIRONMENT_EXPRESSION=environment["TEST_ENVIRONMENT_EXPRESSION"],
        ),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return process.returncode, len(attempts.read_text().splitlines())


def test_the_shard_builds_the_environment_before_running_tests_from_one_expression():
    steps, environment = shard_workflow_steps()
    names = [step.get("name", "") for step in steps]
    build_index = next(
        index
        for index, name in enumerate(names)
        if name.startswith("Build the Python test environment")
    )
    assert names[build_index + 1] == "Run Python tests"
    assert "--max-silent-time 300" in steps[build_index]["run"]
    for step in (steps[build_index], steps[build_index + 1]):
        assert '"$TEST_ENVIRONMENT_EXPRESSION"' in step["run"]
    assert "test-suite-environment.nix" in environment["TEST_ENVIRONMENT_EXPRESSION"]


@pytest.mark.parametrize(
    ("successful_attempt", "expected_status", "expected_attempts"),
    [(1, 0, 1), (3, 0, 3), (4, 1, 3)],
)
def test_the_environment_build_retries_a_stalled_source_build_three_times(
    tmp_path, successful_attempt, expected_status, expected_attempts
):
    status, attempts = run_environment_build_step(tmp_path, successful_attempt)
    assert (status, attempts) == (expected_status, expected_attempts)
