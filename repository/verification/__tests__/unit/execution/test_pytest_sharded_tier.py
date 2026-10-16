import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

VERIFICATION_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def runner(tmp_path):
    repository = tmp_path / "owned repository"
    repository.mkdir()
    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    invocation = tmp_path / "invocation.json"
    fake_pytest = binary_directory / "pytest"
    fake_pytest.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "pathlib.Path(os.environ['INVOCATION']).write_text(json.dumps({"
        "'arguments': sys.argv[1:], 'report_directory': "
        "os.environ.get('DOTFILES_TEST_REPORT_DIRECTORY')}))\n"
        "sys.exit(int(os.environ.get('PYTEST_EXIT_CODE', '0')))\n"
    )
    fake_pytest.chmod(0o755)

    def invoke(names, shard_environment=None, pytest_status=0, selector_status=None):
        if invocation.exists():
            invocation.unlink()
        for name in names:
            path = repository / "fixture/__tests__/integration" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        if selector_status is not None:
            fake_python = binary_directory / "python3"
            fake_python.write_text(
                f"#!{sys.executable}\nraise SystemExit({selector_status})\n"
            )
            fake_python.chmod(0o755)
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$VERIFICATION_ROOT/runner/discovery.sh"\n'
                'source "$VERIFICATION_ROOT/runner/pytest.sh"\n'
                "_run_pytest_tier integration integration-scripts\n",
            ],
            env={
                "PATH": f"{binary_directory}:{os.environ['PATH']}",
                "REPO_DIR": str(repository),
                "VERIFICATION_ROOT": str(VERIFICATION_ROOT),
                "DOTFILES_TEST_REPORT_DIRECTORY": str(tmp_path / "owned reports"),
                "INVOCATION": str(invocation),
                "PYTEST_EXIT_CODE": str(pytest_status),
                **(shard_environment or {}),
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result, json.loads(
            invocation.read_text()
        ) if invocation.exists() else None

    return invoke


def shard_environment(index, count):
    return {
        "DOTFILES_PYTEST_SHARD_INDEX": str(index),
        "DOTFILES_PYTEST_SHARD_COUNT": str(count),
    }


def test_bash_runner_shards_have_disjoint_complete_files_and_distinct_reports(runner):
    names = ["test_a.py", "test_b.py", "test_c.py", "test_d.py", "test_e.py"]
    invocations = [runner(names, shard_environment(index, 2)) for index in range(2)]
    assert all(result.returncode == 0 for result, _ in invocations)
    arguments = [invocation["arguments"] for _, invocation in invocations]
    files = [
        {Path(argument).name for argument in group if argument.endswith(".py")}
        for group in arguments
    ]
    assert files[0].isdisjoint(files[1])
    assert files[0] | files[1] == set(names)
    for index, (_, invocation) in enumerate(invocations):
        assert any(
            argument.endswith(f"pytest-integration-shard-{index}-of-2.xml")
            for argument in invocation["arguments"]
        )
        assert invocation["report_directory"] == ""


def test_bash_runner_preserves_unsharded_report_and_pytest_failure(runner):
    result, invocation = runner(["test_a.py"], pytest_status=7)
    assert result.returncode == 7
    assert invocation["arguments"][0].endswith("pytest-integration.xml")


def test_bash_runner_preserves_sharded_pytest_failure(runner):
    result, invocation = runner(["test_a.py"], shard_environment(0, 2), pytest_status=7)
    assert result.returncode == 7
    assert invocation is not None


def test_bash_runner_empty_shard_does_not_invoke_pytest(runner):
    result, invocation = runner(["test_a.py"], shard_environment(2, 3))
    assert result.returncode == 0
    assert invocation is None


@pytest.mark.parametrize(
    "environment",
    [
        shard_environment(-1, 2),
        shard_environment(2, 2),
        shard_environment(0, 0),
        shard_environment("bad", 2),
        {"DOTFILES_PYTEST_SHARD_INDEX": "0"},
        {"DOTFILES_PYTEST_SHARD_COUNT": "2"},
    ],
)
def test_bash_runner_invalid_shard_does_not_silently_skip_tests(runner, environment):
    result, invocation = runner(["test_a.py"], environment)
    assert result.returncode != 0
    assert invocation is None
    assert "shard" in result.stderr.lower()


def test_bash_runner_rejects_invalid_shard_with_empty_discovery(runner):
    result, invocation = runner([], shard_environment(0, 0))
    assert result.returncode != 0
    assert invocation is None


def test_bash_runner_propagates_selector_failure(runner):
    result, invocation = runner(
        ["test_a.py"], shard_environment(0, 2), selector_status=23
    )
    assert result.returncode == 23
    assert invocation is None
