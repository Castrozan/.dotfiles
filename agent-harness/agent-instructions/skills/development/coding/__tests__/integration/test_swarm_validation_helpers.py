import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "scripts"
BATCH_GATE_SCRIPT = SCRIPTS_DIRECTORY / "swarm-batch-gate.py"
DIFFERENTIAL_CHECK_SCRIPT = SCRIPTS_DIRECTORY / "swarm-differential-check.py"

ORIGINAL_MODULE_SOURCE = """def add(left, right):
    if left == 0:
        return right
    return left + right


def divide(left, right):
    return left / right


def greet(name):
    print(f"hello {name}")
"""


def run_script(script, *arguments, working_directory):
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        capture_output=True,
        text=True,
        cwd=working_directory,
        timeout=120,
    )


def git(repository, *arguments):
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        timeout=60,
    )


@pytest.fixture
def repository_with_committed_module(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "arithmetic.py").write_text(ORIGINAL_MODULE_SOURCE)
    git(tmp_path, "add", "arithmetic.py")
    git(
        tmp_path,
        "-c",
        "user.email=swarm@test",
        "-c",
        "user.name=swarm",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-qm",
        "test: original module",
    )
    return tmp_path


def write_cases(directory, cases):
    cases_path = directory / "cases.json"
    cases_path.write_text(json.dumps(cases))
    return cases_path


def test_batch_gate_reports_each_batch_and_fails_when_one_batch_fails(tmp_path):
    (tmp_path / "clean one.py").write_text("value = 1\n")
    (tmp_path / "clean_two.py").write_text("value = 2\n")
    (tmp_path / "broken.py").write_text("BROKEN\n")
    batches_path = tmp_path / "batches.json"
    batches_path.write_text(
        json.dumps({"good": ["clean one.py", "clean_two.py"], "bad": ["broken.py"]})
    )
    result = run_script(
        BATCH_GATE_SCRIPT,
        "--batches",
        str(batches_path),
        "--check",
        "! grep -l BROKEN {files}",
        working_directory=tmp_path,
    )
    assert result.returncode == 1
    assert "PASS  good" in result.stdout
    assert "FAIL  bad" in result.stdout
    assert "broken.py" in result.stdout
    assert "1 of 2 batch checks passed" in result.stdout


def test_batch_gate_passes_when_every_check_passes_for_every_batch(tmp_path):
    (tmp_path / "module.py").write_text("value = 1\n")
    batches_path = tmp_path / "batches.json"
    batches_path.write_text(json.dumps({"only": ["module.py"]}))
    result = run_script(
        BATCH_GATE_SCRIPT,
        "--batches",
        str(batches_path),
        "--check",
        "test -s {files}",
        "--check",
        "! grep -l BROKEN {files}",
        working_directory=tmp_path,
    )
    assert result.returncode == 0
    assert "2 of 2 batch checks passed" in result.stdout


def test_differential_check_accepts_a_behavior_preserving_refactor(
    repository_with_committed_module,
):
    (repository_with_committed_module / "arithmetic.py").write_text(
        ORIGINAL_MODULE_SOURCE.replace(
            "    if left == 0:\n        return right\n    return left + right",
            "    return right if left == 0 else left + right",
        )
    )
    cases_path = write_cases(
        repository_with_committed_module,
        [
            {"function": "add", "args": [0, 5]},
            {"function": "add", "args": [2, 3]},
            {"function": "divide", "args": [1, 0]},
            {"function": "greet", "kwargs": {"name": "partner"}},
        ],
    )
    result = run_script(
        DIFFERENTIAL_CHECK_SCRIPT,
        "--path",
        "arithmetic.py",
        "--cases",
        str(cases_path),
        working_directory=repository_with_committed_module,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "4 of 4 cases behave identically" in result.stdout


def test_differential_check_reports_changed_results_and_missing_functions(
    repository_with_committed_module,
):
    (repository_with_committed_module / "arithmetic.py").write_text(
        ORIGINAL_MODULE_SOURCE.replace("left + right", "left - right").replace(
            "def greet(name)", "def welcome(name)"
        )
    )
    cases_path = write_cases(
        repository_with_committed_module,
        [
            {"function": "add", "args": [2, 3]},
            {"function": "greet", "args": ["partner"]},
            {"function": "divide", "args": [6, 3]},
        ],
    )
    result = run_script(
        DIFFERENTIAL_CHECK_SCRIPT,
        "--path",
        "arithmetic.py",
        "--cases",
        str(cases_path),
        working_directory=repository_with_committed_module,
    )
    assert result.returncode == 1
    assert result.stdout.count("MISMATCH") == 2
    assert "1 of 3 cases behave identically" in result.stdout
