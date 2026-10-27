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
    assert [package["outputs"]["out"] for package in packages] == DEPLOYED_PATCHED_PACKAGES
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
