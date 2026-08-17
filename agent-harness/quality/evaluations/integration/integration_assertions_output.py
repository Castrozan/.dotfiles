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
from integration_assertions_workspace import (
    check_workspace_file_changed_assertion,
    check_workspace_file_not_contains_assertion,
)


def check_output_contains_assertion(
    trace: SessionTrace,
    expected_substring: str,
) -> AssertionResult:
    final_output = (
        trace.assistant_messages[-1].lower() if trace.assistant_messages else ""
    )
    found = expected_substring.lower() in final_output
    return AssertionResult(
        name=f"output contains '{expected_substring}'",
        passed=found,
        detail=("found" if found else "not found in assistant output"),
    )


def check_output_not_contains_assertion(
    trace: SessionTrace,
    forbidden_substring: str,
) -> AssertionResult:
    final_output = (
        trace.assistant_messages[-1].lower() if trace.assistant_messages else ""
    )
    absent = forbidden_substring.lower() not in final_output
    return AssertionResult(
        name=(f"output does not contain '{forbidden_substring}'"),
        passed=absent,
        detail=("correctly absent" if absent else "found in assistant output"),
    )


def check_output_maximum_words_assertion(
    trace: SessionTrace,
    maximum_words: int,
) -> AssertionResult:
    final_output = trace.assistant_messages[-1] if trace.assistant_messages else ""
    word_count = len(final_output.split())
    return AssertionResult(
        name=f"final output uses at most {maximum_words} words",
        passed=word_count <= maximum_words,
        detail=f"found {word_count} words",
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

    if "output_maximum_words" in assertions:
        results.append(
            check_output_maximum_words_assertion(
                trace, assertions["output_maximum_words"]
            )
        )

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
