from e2e_models import E2eAssertionResult, TerminalSessionTrace
from e2e_trace import (
    COLLAPSED_BASH_ARGUMENTS_TEXT,
    extract_invoked_skill_names_from_trace,
    extract_tool_name_sequence,
)


def check_autonomous_skill_invocation_assertion(
    trace: TerminalSessionTrace,
    expected_skill_name: str,
) -> E2eAssertionResult:
    invoked_skills = extract_invoked_skill_names_from_trace(trace)
    present = expected_skill_name in invoked_skills
    return E2eAssertionResult(
        name=f"autonomously invokes Skill({expected_skill_name})",
        passed=present,
        detail=(
            f"Skill({expected_skill_name}) called (all: {invoked_skills})"
            if present
            else (
                f"Skill({expected_skill_name}) never invoked. "
                f"Skills called: {invoked_skills or 'none'}"
            )
        ),
    )


def check_wrong_skill_not_invoked_assertion(
    trace: TerminalSessionTrace,
    forbidden_skill_name: str,
) -> E2eAssertionResult:
    invoked_skills = extract_invoked_skill_names_from_trace(trace)
    present = forbidden_skill_name in invoked_skills
    return E2eAssertionResult(
        name=f"does NOT invoke wrong Skill({forbidden_skill_name})",
        passed=not present,
        detail=(
            f"wrong skill invoked (all: {invoked_skills})"
            if present
            else f"correctly avoided {forbidden_skill_name}"
        ),
    )


def check_terminal_tool_presence_assertion(
    trace: TerminalSessionTrace,
    required_tool: str,
) -> E2eAssertionResult:
    tool_names = extract_tool_name_sequence(trace)
    present = required_tool in tool_names
    count = tool_names.count(required_tool)
    return E2eAssertionResult(
        name=f"uses {required_tool}",
        passed=present,
        detail=(
            f"{required_tool} called {count} time(s)"
            if present
            else (f"{required_tool} never called. Tools: {tool_names}")
        ),
    )


def check_terminal_tool_ordering_assertion(
    trace: TerminalSessionTrace,
    assertion: dict,
) -> E2eAssertionResult:
    first_tool = assertion["tool"]
    second_tool = assertion["before"]
    tool_names = extract_tool_name_sequence(trace)

    first_index = next(
        (i for i, n in enumerate(tool_names) if n == first_tool),
        None,
    )
    second_index = next(
        (i for i, n in enumerate(tool_names) if n == second_tool),
        None,
    )

    if first_index is None:
        return E2eAssertionResult(
            name=f"{first_tool} before {second_tool}",
            passed=False,
            detail=f"{first_tool} never called",
        )
    if second_index is None:
        return E2eAssertionResult(
            name=f"{first_tool} before {second_tool}",
            passed=False,
            detail=f"{second_tool} never called",
        )

    passed = first_index < second_index
    return E2eAssertionResult(
        name=f"{first_tool} before {second_tool}",
        passed=passed,
        detail=(
            f"order correct ({first_index} < {second_index})"
            if passed
            else f"wrong order ({first_index} >= {second_index})"
        ),
    )


def check_bash_command_contains_assertion(
    trace: TerminalSessionTrace,
    expected_substring: str,
) -> E2eAssertionResult:
    matching = [
        cmd for cmd in trace.detected_bash_commands if expected_substring in cmd
    ]
    return E2eAssertionResult(
        name=f"bash ran '{expected_substring}'",
        passed=bool(matching),
        detail=(
            f"ran {matching[0]}"
            if matching
            else f"no Bash call matched among {trace.detected_bash_commands}"
        ),
    )


def check_bash_command_not_contains_assertion(
    trace: TerminalSessionTrace,
    forbidden_substring: str,
) -> E2eAssertionResult:
    matching = [
        cmd for cmd in trace.detected_bash_commands if forbidden_substring in cmd
    ]
    if matching:
        return E2eAssertionResult(
            name=f"did not run '{forbidden_substring}'",
            passed=False,
            detail=f"ran {matching[0]}",
        )
    collapsed = trace.detected_bash_commands.count(COLLAPSED_BASH_ARGUMENTS_TEXT)
    if collapsed:
        return E2eAssertionResult(
            name=f"did not run '{forbidden_substring}'",
            passed=False,
            detail=(
                f"{collapsed} shell command(s) ran with their arguments collapsed out "
                f"of the transcript, so absence cannot be proven from this trace"
            ),
        )
    return E2eAssertionResult(
        name=f"did not run '{forbidden_substring}'",
        passed=True,
        detail="correctly absent",
    )
