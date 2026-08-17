import subprocess
from pathlib import Path

from integration_models import AssertionResult


def check_workspace_file_not_contains_assertion(
    workspace_directory: Path,
    file_path: str,
    forbidden_pattern: str,
) -> AssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return AssertionResult(
            name=f"{file_path} does not contain '{forbidden_pattern}'",
            passed=False,
            detail=f"file {file_path} does not exist",
        )
    absent = forbidden_pattern not in full_path.read_text()
    return AssertionResult(
        name=f"{file_path} does not contain '{forbidden_pattern}'",
        passed=absent,
        detail="correctly absent from file" if absent else "found in file content",
    )


def check_workspace_file_changed_assertion(
    workspace_directory: Path,
    file_path: str,
) -> AssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail=f"file {file_path} does not exist",
        )
    try:
        initial_commit = (
            subprocess.run(
                ["git", "rev-list", "--max-parents=0", "HEAD"],
                capture_output=True,
                text=True,
                cwd=workspace_directory,
                timeout=5,
            )
            .stdout.strip()
            .split("\n")[0]
        )
        committed_changes = (
            subprocess.run(
                ["git", "diff", "--name-only", initial_commit, "HEAD"],
                capture_output=True,
                text=True,
                cwd=workspace_directory,
                timeout=5,
            )
            .stdout.strip()
            .split("\n")
        )
        uncommitted_changes = (
            subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=workspace_directory,
                timeout=5,
            )
            .stdout.strip()
            .split("\n")
        )
        all_changed_files = set(committed_changes + uncommitted_changes)
        was_changed = file_path in all_changed_files
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else f"file unchanged. Changed: {list(all_changed_files)}"
            ),
        )
    except Exception:
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )
