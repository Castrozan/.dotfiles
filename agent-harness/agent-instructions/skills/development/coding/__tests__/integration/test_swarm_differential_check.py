import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "scripts"
DIFFERENTIAL_CHECK_SCRIPT = SCRIPTS_DIRECTORY / "swarm-differential-check.py"

ORIGINAL_GREETING_SCRIPT = """name="$1"
if [ -z "$name" ]; then
  name=stranger
fi
echo "hello $name"
"""


def git(repository, *arguments):
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        timeout=60,
    )


def run_differential_check(repository, *arguments):
    return subprocess.run(
        [sys.executable, str(DIFFERENTIAL_CHECK_SCRIPT), *arguments],
        capture_output=True,
        text=True,
        cwd=repository,
        timeout=120,
    )


@pytest.fixture
def repository_with_committed_scripts(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "greet.sh").write_text(ORIGINAL_GREETING_SCRIPT)
    (tmp_path / "notes.txt").write_text("unchanged\n")
    git(tmp_path, "add", ".")
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
        "test: original scripts",
    )
    return tmp_path


def test_differential_check_accepts_a_behavior_preserving_refactor(
    repository_with_committed_scripts,
):
    (repository_with_committed_scripts / "tools" / "greet.sh").write_text(
        'echo "hello ${1:-stranger}"\n'
    )
    result = run_differential_check(
        repository_with_committed_scripts,
        "--check",
        "bash tools/greet.sh",
        "--check",
        "bash tools/greet.sh partner",
        "--check",
        "pwd",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 files modified since HEAD" in result.stdout
    assert "3 of 3 checks behave identically" in result.stdout


def test_differential_check_reports_changed_stdout_and_exit_status(
    repository_with_committed_scripts,
):
    (repository_with_committed_scripts / "tools" / "greet.sh").write_text(
        'echo "hi ${1:-stranger}"\necho broken >&2\nexit 3\n'
    )
    result = run_differential_check(
        repository_with_committed_scripts,
        "--check",
        "bash tools/greet.sh partner",
        "--check",
        "cat notes.txt",
    )
    assert result.returncode == 1
    assert "DIFFERS  bash tools/greet.sh partner" in result.stdout
    assert "HEAD: exit 0, working tree: exit 3" in result.stdout
    assert "+hi partner" in result.stdout
    assert "stderr at working tree:\n    broken" in result.stdout
    assert "1 of 2 checks behave identically" in result.stdout


def test_differential_check_expands_files_to_the_modified_files_in_scope(
    repository_with_committed_scripts,
):
    (repository_with_committed_scripts / "tools" / "greet.sh").write_text(
        ORIGINAL_GREETING_SCRIPT + "\n"
    )
    (repository_with_committed_scripts / "notes.txt").write_text("edited\n")
    result = run_differential_check(
        repository_with_committed_scripts,
        "--path",
        "tools",
        "--check",
        "echo {files}",
        "--check",
        "for file in {files}; do bash $file partner; done",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 files modified since HEAD" in result.stdout
    assert "2 of 2 checks behave identically" in result.stdout
