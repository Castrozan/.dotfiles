import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

REPOSITORY = Path(__file__).resolve().parents[5]
WORKFLOW = REPOSITORY / ".github/workflows/nix-binary-cache.yml"
CACHE_CONFIGURATION = Path(
    "machine-configuration/development/system-rebuild/dotfiles-binary-cache.json"
)


@pytest.fixture
def cache_workflow(tmp_path):
    configuration = tmp_path / CACHE_CONFIGURATION
    configuration.parent.mkdir(parents=True)
    shutil.copyfile(REPOSITORY / CACHE_CONFIGURATION, configuration)
    executable = tmp_path / "nix"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "arguments = sys.argv[1:]\n"
        "with Path('nix-calls.jsonl').open('a') as calls:\n"
        "    calls.write(json.dumps(arguments) + '\\n')\n"
        "if arguments[0] == os.environ.get('NIX_FAILURE_COMMAND'):\n"
        "    raise SystemExit(19)\n"
        "if arguments[0] == 'eval':\n"
        "    print('/nix/store/test-environment')\n"
        "elif arguments[0] == 'build':\n"
        "    names = ['test-environment'] if '--expr' in arguments else "
        "[argument.rsplit('.', 1)[1] for argument in arguments "
        "if argument.startswith('.#packages.')]\n"
        "    print(json.dumps([{'outputs': {'out': '/nix/store/' + name}} "
        "for name in names]))\n"
    )
    executable.chmod(0o755)
    return tmp_path


def execute_step(directory, job, name, **environment):
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"][job]["steps"]
    script = next(step["run"] for step in steps if step.get("name") == name)
    return subprocess.run(
        [shutil.which("bash"), "-e", "-o", "pipefail", "-c", script],
        cwd=directory,
        env=dict(os.environ, PATH=f"{directory}:{os.environ['PATH']}", **environment),
        capture_output=True,
        text=True,
        timeout=10,
    )


DEPLOYED_PATCHED_PACKAGES = [
    "/nix/store/herdr",
    "/nix/store/herdr-agent-resume",
    "/nix/store/herdr-annotate",
    "/nix/store/codex",
    "/nix/store/wezterm",
]


def test_the_signed_manifest_retains_deployed_packages_and_the_test_environment(
    cache_workflow,
):
    process = execute_step(
        cache_workflow,
        "publish",
        "Build the patched packages and Python test environment",
        NIX_SYSTEM="x86_64-linux",
    )
    assert process.returncode == 0, process.stderr
    packages = json.loads((cache_workflow / "binary-cache-packages.json").read_text())
    assert [package["outputs"]["out"] for package in packages] == [
        *DEPLOYED_PATCHED_PACKAGES,
        "/nix/store/test-environment",
    ]


def test_the_darwin_manifest_holds_the_patched_packages_for_its_own_system(
    cache_workflow,
):
    process = execute_step(
        cache_workflow,
        "publish",
        "Build the patched packages and Python test environment",
        NIX_SYSTEM="aarch64-darwin",
    )
    assert process.returncode == 0, process.stderr
    packages = json.loads((cache_workflow / "binary-cache-packages.json").read_text())
    assert [
        package["outputs"]["out"] for package in packages
    ] == DEPLOYED_PATCHED_PACKAGES
    calls = [
        json.loads(line)
        for line in (cache_workflow / "nix-calls.jsonl").read_text().splitlines()
    ]
    assert len(calls) == 1
    assert all(
        argument.startswith(".#packages.aarch64-darwin.")
        for argument in calls[0]
        if argument.startswith(".#")
    )


def test_a_failed_signed_copy_cannot_fall_back_to_local_construction(cache_workflow):
    process = execute_step(
        cache_workflow,
        "substitute",
        "Copy the exact Python test environment from the signed cache",
        NIX_FAILURE_COMMAND="copy",
    )
    assert process.returncode == 19
    calls = [
        json.loads(line)
        for line in (cache_workflow / "nix-calls.jsonl").read_text().splitlines()
    ]
    assert [arguments[0] for arguments in calls] == ["eval", "copy"]
    assert not (
        cache_workflow / "binary-cache-test-environment-substitutions.json"
    ).exists()


def test_a_successful_signed_copy_precedes_environment_realization(cache_workflow):
    process = execute_step(
        cache_workflow,
        "substitute",
        "Copy the exact Python test environment from the signed cache",
    )
    assert process.returncode == 0, process.stderr
    calls = [
        json.loads(line)
        for line in (cache_workflow / "nix-calls.jsonl").read_text().splitlines()
    ]
    assert [arguments[0] for arguments in calls] == ["eval", "copy", "build"]
    configuration = json.loads((cache_workflow / CACHE_CONFIGURATION).read_text())
    assert calls[1] == [
        "copy",
        "--from",
        configuration["url"],
        "/nix/store/test-environment",
        "--extra-trusted-public-keys",
        configuration["publicKey"],
    ]
    assert "--always-allow-substitutes" in calls[2]


def test_the_consumer_appends_the_existing_cache_without_overwriting_settings(
    cache_workflow,
):
    workflow = yaml.safe_load(
        (REPOSITORY / ".github/workflows/python-test-shard.yml").read_text()
    )
    script = next(
        step["run"]
        for step in workflow["jobs"]["python"]["steps"]
        if step.get("name") == "Configure the signed Python environment cache"
    )
    home = cache_workflow / "home"
    configuration = home / ".config/nix/nix.conf"
    configuration.parent.mkdir(parents=True)
    configuration.write_text("experimental-features = nix-command flakes\n")
    process = subprocess.run(
        [shutil.which("bash"), "-e", "-c", script],
        cwd=cache_workflow,
        env=dict(os.environ, HOME=str(home)),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr
    cache = json.loads((cache_workflow / CACHE_CONFIGURATION).read_text())
    assert configuration.read_text() == (
        "experimental-features = nix-command flakes\n"
        f"extra-substituters = {cache['url']}\n"
        f"extra-trusted-public-keys = {cache['publicKey']}\n"
    )


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
