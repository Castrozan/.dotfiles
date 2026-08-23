from pathlib import Path

from e2e_models import E2eAssertionResult, TerminalSessionTrace
from e2e_trace import extract_tool_name_sequence


def calculate_e2e_experience_score(
    trace: TerminalSessionTrace,
    assertion_results: list[E2eAssertionResult],
    workspace_directory: Path | None = None,
) -> int:
    score = 65
    tool_names = extract_tool_name_sequence(trace)
    edit_count = tool_names.count("Edit") + tool_names.count("Write")

    for command in trace.detected_bash_commands:
        if "git add -A" in command or "git add ." in command:
            score -= 10
            break

    bash_misuse_commands = ["cat ", "head ", "tail ", "find ."]
    for command in trace.detected_bash_commands:
        for bad_pattern in bash_misuse_commands:
            if bad_pattern in command:
                score -= 5
                break

    formatter_ran = any(
        pattern in trace.raw_terminal_output
        for pattern in ("ruff", "nixfmt", "shfmt", "shellcheck")
    )
    if edit_count > 0 and formatter_ran:
        score += 5

    if assertion_results:
        passed = sum(1 for assertion in assertion_results if assertion.passed)
        failed = len(assertion_results) - passed
        score += passed * 3
        score -= failed * 8

    return max(0, min(score, 100))


def check_minimum_e2e_experience_score(score: int, minimum: int) -> E2eAssertionResult:
    return E2eAssertionResult(
        name=f"experience score is at least {minimum}",
        passed=score >= minimum,
        detail=f"found {score}",
    )
