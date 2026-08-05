import subprocess
from pathlib import Path

from integration_assertions_tools import (
    check_minimum_tool_count_assertion,
    check_read_to_edit_ratio_assertion,
    check_tool_absence_assertion,
    check_tool_ordering_assertion,
    check_tool_presence_assertion,
)
from integration_models import AssertionResult, SessionTrace
from integration_session import collect_written_file_content_from_tool_calls


def check_output_contains_assertion(
    trace: SessionTrace,
    expected_substring: str,
) -> AssertionResult:
    combined_output = " ".join(trace.assistant_messages).lower()
    found = expected_substring.lower() in combined_output
    return AssertionResult(
        name=f"output contains '{expected_substring}'",
        passed=found,
        detail=("found" if found else "not found in assistant output"),
    )


def check_output_not_contains_assertion(
    trace: SessionTrace,
    forbidden_substring: str,
) -> AssertionResult:
    combined_output = " ".join(trace.assistant_messages).lower()
    absent = forbidden_substring.lower() not in combined_output
    return AssertionResult(
        name=(f"output does not contain '{forbidden_substring}'"),
        passed=absent,
        detail=("correctly absent" if absent else "found in assistant output"),
    )


def check_written_code_not_contains_assertion(
    trace: SessionTrace,
    forbidden_pattern: str,
) -> AssertionResult:
    written_content = collect_written_file_content_from_tool_calls(trace)
    if not written_content:
        return AssertionResult(
            name=(f"written code does not contain '{forbidden_pattern}'"),
            passed=True,
            detail="no code written via Edit/Write",
        )
    absent = forbidden_pattern not in written_content
    return AssertionResult(
        name=(f"written code does not contain '{forbidden_pattern}'"),
        passed=absent,
        detail=(
            "correctly absent from written code"
            if absent
            else "found in code written via Edit/Write"
        ),
    )


def check_workspace_file_not_contains_assertion(
    workspace_directory: Path,
    file_path: str,
    forbidden_pattern: str,
) -> AssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return AssertionResult(
            name=(f"{file_path} does not contain '{forbidden_pattern}'"),
            passed=False,
            detail=f"file {file_path} does not exist",
        )
    content = full_path.read_text()
    absent = forbidden_pattern not in content
    return AssertionResult(
        name=(f"{file_path} does not contain '{forbidden_pattern}'"),
        passed=absent,
        detail=("correctly absent from file" if absent else "found in file content"),
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
        initial_commit_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        initial_commit_sha = initial_commit_result.stdout.strip().split("\n")[0]

        diff_result = subprocess.run(
            ["git", "diff", "--name-only", initial_commit_sha, "HEAD"],
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
        uncommitted_changes = uncommitted_result.stdout.strip().split("\n")

        all_changed_files = set(committed_changes + uncommitted_changes)
        was_changed = file_path in all_changed_files
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else (
                    f"file unchanged since initial commit. "
                    f"Changed: {list(all_changed_files)}"
                )
            ),
        )
    except Exception:
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )


def run_assertions(
    trace: SessionTrace,
    assertions: dict,
    workspace_directory: Path | None = None,
) -> list[AssertionResult]:
    results = []

    for ordering in assertions.get("tool_order", []):
        results.append(check_tool_ordering_assertion(trace, ordering))

    for required_tool in assertions.get("tool_presence", []):
        results.append(check_tool_presence_assertion(trace, required_tool))

    for forbidden_tool in assertions.get("tool_absence", []):
        results.append(check_tool_absence_assertion(trace, forbidden_tool))

    for expected in assertions.get("output_contains", []):
        results.append(check_output_contains_assertion(trace, expected))

    for forbidden in assertions.get("output_not_contains", []):
        results.append(check_output_not_contains_assertion(trace, forbidden))

    for forbidden in assertions.get("written_code_not_contains", []):
        results.append(check_written_code_not_contains_assertion(trace, forbidden))

    if workspace_directory:
        for file_check in assertions.get("file_not_contains", []):
            results.append(
                check_workspace_file_not_contains_assertion(
                    workspace_directory,
                    file_check["file"],
                    file_check["pattern"],
                )
            )

        for file_path in assertions.get("file_changed", []):
            results.append(
                check_workspace_file_changed_assertion(workspace_directory, file_path)
            )

    if "read_to_edit_ratio" in assertions:
        results.append(
            check_read_to_edit_ratio_assertion(trace, assertions["read_to_edit_ratio"])
        )

    for tool_count in assertions.get("minimum_tool_count", []):
        results.append(
            check_minimum_tool_count_assertion(
                trace,
                tool_count["tool"],
                tool_count["count"],
            )
        )

    return results
