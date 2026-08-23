import subprocess
from pathlib import Path

from e2e_models import E2eAssertionResult


def check_workspace_file_changed_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    try:
        initial_commit_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        initial_sha = initial_commit_result.stdout.strip().split("\n")[0]

        diff_result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                initial_sha,
                "HEAD",
            ],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        committed_changes = diff_result.stdout.strip().split("\n")

        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        uncommitted = uncommitted_result.stdout.strip().split("\n")

        all_changed = set(committed_changes + uncommitted)
        was_changed = file_path in all_changed
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else f"unchanged. Changed: {list(all_changed)}"
            ),
        )
    except Exception:
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )


def check_workspace_formatted_correctly_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=False,
            detail="file does not exist",
        )

    if file_path.endswith(".py"):
        result = subprocess.run(
            ["ruff", "check", "--select=E,F,W", str(full_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        passed = result.returncode == 0
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=passed,
            detail=(
                "ruff check passed" if passed else f"ruff errors: {result.stdout[:200]}"
            ),
        )

    return E2eAssertionResult(
        name=f"{file_path} is formatted",
        passed=True,
        detail="no formatter check available",
    )
