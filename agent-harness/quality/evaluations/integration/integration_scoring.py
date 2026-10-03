from integration_models import AssertionResult, SessionTrace
from integration_session import (
    collect_written_file_content_from_tool_calls,
    extract_tool_name_sequence,
)


def detect_bash_tool_misuse(trace: SessionTrace) -> int:
    penalty = 0
    for tool_call in trace.tool_calls:
        if tool_call.tool_name != "Bash":
            continue
        command = tool_call.tool_input.get("command", "")
        penalty += _bash_command_misuse_penalty(command)
    return max(penalty, -25)


def _bash_command_misuse_penalty(command):
    return (
        _file_read_command_penalty(command)
        + _find_command_penalty(command)
        + _grep_command_penalty(command)
        + _git_staging_command_penalty(command)
    )


def _file_read_command_penalty(command):
    if any(
        pattern in command
        for pattern in (
            "cat ",
            "head ",
            "tail ",
            "sed ",
        )
    ):
        return -5
    return 0


def _find_command_penalty(command):
    if "find " in command and "find ." in command:
        return -5
    return 0


def _grep_command_penalty(command):
    if command.startswith("grep ") or " grep " in command:
        return -5
    return 0


def _git_staging_command_penalty(command):
    if "git add -A" in command or "git add ." in command:
        return -10
    return 0


def calculate_experience_score(
    trace: SessionTrace,
    assertion_results: list[AssertionResult],
) -> int:
    score = 65
    tool_sequence = extract_tool_name_sequence(trace)
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")

    score += _read_edit_score_adjustment(tool_sequence, read_count, edit_count)
    written_content = collect_written_file_content_from_tool_calls(trace)
    score += _written_code_score_adjustment(written_content)
    score += detect_bash_tool_misuse(trace)
    score += _assertion_score_adjustment(assertion_results)
    return max(0, min(score, 100))


def _read_edit_score_adjustment(tool_sequence, read_count, edit_count):
    if edit_count > 0:
        if read_count == 0:
            return -20
        score = 10 if _read_precedes_edit(tool_sequence) else -15
        return score + _read_edit_ratio_adjustment(read_count / edit_count)
    return 0


def _read_precedes_edit(tool_sequence):
    first_read_index = _first_tool_index(tool_sequence, ("Read",))
    first_edit_index = _first_tool_index(tool_sequence, ("Edit", "Write"))
    return first_read_index < first_edit_index


def _first_tool_index(tool_sequence, tool_names):
    return next(
        (index for index, name in enumerate(tool_sequence) if name in tool_names),
        999,
    )


def _read_edit_ratio_adjustment(read_to_edit_ratio):
    if read_to_edit_ratio >= 2.0:
        return 10
    if read_to_edit_ratio >= 1.0:
        return 5
    return 0


def _written_code_score_adjustment(written_content):
    if written_content:
        comment_patterns = ("# ", "// ", "/* ", "# TODO", "# FIXME", "# NOTE")
        comment_count = sum(
            written_content.count(pattern) for pattern in comment_patterns
        )
        if comment_count == 0:
            return 10
        if comment_count <= 2:
            return -5
        return -15
    return 0


def _assertion_score_adjustment(assertion_results):
    if assertion_results:
        passed_count = sum(
            1 for assertion_result in assertion_results if assertion_result.passed
        )
        failed_count = len(assertion_results) - passed_count
        return passed_count * 3 - failed_count * 8
    return 0


def check_minimum_experience_score(score: int, minimum: int) -> AssertionResult:
    return AssertionResult(
        name=f"experience score is at least {minimum}",
        passed=score >= minimum,
        detail=f"found {score}",
    )
