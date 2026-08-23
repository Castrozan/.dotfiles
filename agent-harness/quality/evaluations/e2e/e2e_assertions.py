from pathlib import Path

from e2e_assertions_naming import check_workspace_file_descriptive_names_assertion
from e2e_assertions_output import (
    check_output_contains_assertion,
    check_output_maximum_words_assertion,
    check_output_not_contains_assertion,
)
from e2e_assertions_skills_tools import (
    check_autonomous_skill_invocation_assertion,
    check_bash_command_contains_assertion,
    check_bash_command_not_contains_assertion,
    check_terminal_tool_ordering_assertion,
    check_terminal_tool_presence_assertion,
    check_wrong_skill_not_invoked_assertion,
)
from e2e_assertions_comments import check_workspace_file_no_comments_assertion
from e2e_assertions_workspace import (
    check_workspace_file_changed_assertion,
    check_workspace_formatted_correctly_assertion,
)
from e2e_models import E2eAssertionResult, TerminalSessionTrace


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
    for skill_name in assertions.get("autonomous_skill_invocation", []):
        results.append(check_autonomous_skill_invocation_assertion(trace, skill_name))
    for skill_name in assertions.get("wrong_skill_not_invoked") or []:
        results.append(check_wrong_skill_not_invoked_assertion(trace, skill_name))
    for expected in assertions.get("bash_command_contains", []):
        results.append(check_bash_command_contains_assertion(trace, expected))
    for forbidden in assertions.get("bash_command_not_contains", []):
        results.append(check_bash_command_not_contains_assertion(trace, forbidden))
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
    if workspace_directory:
        for file_path in assertions.get("workspace_file_no_comments", []):
            results.append(
                check_workspace_file_no_comments_assertion(
                    workspace_directory, file_path
                )
            )
        for file_path in assertions.get("workspace_file_descriptive_names", []):
            results.append(
                check_workspace_file_descriptive_names_assertion(
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
