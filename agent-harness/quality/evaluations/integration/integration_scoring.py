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
        if any(
            pattern in command
            for pattern in (
                "cat ",
                "head ",
                "tail ",
                "sed ",
            )
        ):
            penalty -= 5
        if "find " in command and "find ." in command:
            penalty -= 5
        if command.startswith("grep ") or " grep " in command:
            penalty -= 5
        if "git add -A" in command or "git add ." in command:
            penalty -= 10
    return max(penalty, -25)


def detect_em_dashes_in_output(
    trace: SessionTrace,
) -> int:
    combined_output = " ".join(trace.assistant_messages)
    em_dash_count = combined_output.count("—")
    if em_dash_count > 0:
        return -5
    return 0


def detect_over_explanation(
    trace: SessionTrace,
) -> int:
    combined_output = " ".join(trace.assistant_messages)
    word_count = len(combined_output.split())
    tool_count = len(trace.tool_calls)

    if tool_count == 0 and word_count > 200:
        return -10
    if tool_count > 0 and word_count > 500:
        return -5
    return 0


def calculate_experience_score(
    trace: SessionTrace,
    assertion_results: list[AssertionResult],
) -> int:
    score = 50
    tool_sequence = extract_tool_name_sequence(trace)
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")

    if edit_count > 0:
        if read_count == 0:
            score -= 20
        else:
            first_read_index = next(
                (index for index, name in enumerate(tool_sequence) if name == "Read"),
                999,
            )
            first_edit_index = next(
                (
                    index
                    for index, name in enumerate(tool_sequence)
                    if name in ("Edit", "Write")
                ),
                999,
            )
            if first_read_index < first_edit_index:
                score += 10
            else:
                score -= 15

            read_to_edit_ratio = read_count / edit_count
            if read_to_edit_ratio >= 2.0:
                score += 10
            elif read_to_edit_ratio >= 1.0:
                score += 5
    elif len(tool_sequence) > 0:
        score -= 10

    written_content = collect_written_file_content_from_tool_calls(trace)
    if written_content:
        comment_patterns = (
            "# ",
            "// ",
            "/* ",
            "# TODO",
            "# FIXME",
            "# NOTE",
        )
        comment_count = sum(
            written_content.count(pattern) for pattern in comment_patterns
        )
        if comment_count == 0:
            score += 10
        elif comment_count <= 2:
            score -= 5
        else:
            score -= 15

    score += detect_bash_tool_misuse(trace)
    score += detect_em_dashes_in_output(trace)
    score += detect_over_explanation(trace)

    if assertion_results:
        passed_count = sum(
            1 for assertion_result in assertion_results if assertion_result.passed
        )
        failed_count = len(assertion_results) - passed_count
        score += passed_count * 3
        score -= failed_count * 8

    return max(0, min(score, 100))
