import subprocess
from pathlib import Path

from e2e_assertions_skills_tools import (
    check_autonomous_skill_invocation_assertion,
    check_bash_command_contains_assertion,
    check_bash_command_not_contains_assertion,
    check_terminal_tool_ordering_assertion,
    check_terminal_tool_presence_assertion,
    check_wrong_skill_not_invoked_assertion,
)
from e2e_models import E2eAssertionResult, TerminalSessionTrace


def check_workspace_file_no_comments_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=False,
            detail="file does not exist",
        )
    content = full_path.read_text()
    comment_patterns = ["# ", "// ", "/* ", "# TODO", "# FIXME"]
    found_comments = [p for p in comment_patterns if p in content]
    if not found_comments:
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=True,
            detail="no comments found",
        )

    shebang_only = (
        found_comments == ["# "]
        and content.startswith("#!")
        and content.count("# ") == 1
    )
    if shebang_only:
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=True,
            detail="only shebang line",
        )

    return E2eAssertionResult(
        name=f"{file_path} has no comments",
        passed=False,
        detail=f"found: {found_comments}",
    )


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


def run_e2e_assertions(
    trace: TerminalSessionTrace,
    assertions: dict,
    workspace_directory: Path | None = None,
) -> list[E2eAssertionResult]:
    results = []

    for ordering in assertions.get("tool_order", []):
        results.append(check_terminal_tool_ordering_assertion(trace, ordering))

    for required_tool in assertions.get("tool_presence", []):
        results.append(check_terminal_tool_presence_assertion(trace, required_tool))

    for expected_skill_name in assertions.get("autonomous_skill_invocation", []):
        results.append(
            check_autonomous_skill_invocation_assertion(trace, expected_skill_name)
        )

    for forbidden_skill_name in assertions.get("wrong_skill_not_invoked", []):
        results.append(
            check_wrong_skill_not_invoked_assertion(trace, forbidden_skill_name)
        )

    for expected in assertions.get("bash_command_contains", []):
        results.append(check_bash_command_contains_assertion(trace, expected))

    for forbidden in assertions.get("bash_command_not_contains", []):
        results.append(check_bash_command_not_contains_assertion(trace, forbidden))

    if workspace_directory:
        for file_path in assertions.get("workspace_file_no_comments", []):
            results.append(
                check_workspace_file_no_comments_assertion(
                    workspace_directory, file_path
                )
            )

        for file_path in assertions.get("file_changed", []):
            results.append(
                check_workspace_file_changed_assertion(workspace_directory, file_path)
            )

        for file_path in assertions.get("workspace_formatted", []):
            results.append(
                check_workspace_formatted_correctly_assertion(
                    workspace_directory, file_path
                )
            )

    return results
