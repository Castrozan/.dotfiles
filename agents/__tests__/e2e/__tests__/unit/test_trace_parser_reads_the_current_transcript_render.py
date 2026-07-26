from e2e_assertions_skills_tools import check_bash_command_not_contains_assertion
from e2e_trace import build_terminal_session_trace

MODERN_TRANSCRIPT = (
    "\n"
    "⏺ Update(src/parser.py)\n"
    "  ⎿  Added 4 lines, removed 1 line\n"
    "\n"
    "  Ran 2 shell commands\n"
    "\n"
    "⏺ Only src/parser.py is modified, matching what I intended to change.\n"
)

LEGACY_TRANSCRIPT = (
    "● Read(src/parser.py)\n"
    "● Bash(git add src/parser.py)\n"
    "● Done, staged the one file.\n"
)


def trace_of(raw_output):
    return build_terminal_session_trace(
        raw_output, duration_seconds=1.0, timed_out=False
    )


def test_the_current_record_bullet_is_recognised_as_a_tool_call():
    tool_names = [
        call.tool_name for call in trace_of(MODERN_TRANSCRIPT).detected_tool_calls
    ]
    assert "Edit" in tool_names, (
        "Claude Code renders tool calls with the record bullet, so a parser that only "
        f"knows the old bullets reports an empty trajectory: {tool_names}"
    )


def test_the_legacy_bullet_still_parses():
    tool_names = [
        call.tool_name for call in trace_of(LEGACY_TRANSCRIPT).detected_tool_calls
    ]
    assert tool_names == ["Read", "Bash"]


def test_assistant_text_is_extracted_from_the_current_bullet():
    assert any(
        "Only src/parser.py is modified" in block
        for block in trace_of(MODERN_TRANSCRIPT).detected_assistant_text_blocks
    )


def test_collapsed_shell_runs_are_counted_as_bash_calls():
    assert (
        trace_of(MODERN_TRANSCRIPT).detected_bash_commands.count(
            "<collapsed by the transcript>"
        )
        == 2
    )


def test_a_negative_bash_assertion_cannot_pass_over_collapsed_arguments():
    result = check_bash_command_not_contains_assertion(
        trace_of(MODERN_TRANSCRIPT), "git add -A"
    )
    assert not result.passed, (
        "the transcript hid what those two shell commands were, so reporting the "
        "forbidden command as absent is a vacuous pass"
    )
    assert "collapsed" in result.detail


def test_a_negative_bash_assertion_still_passes_when_every_command_is_visible():
    result = check_bash_command_not_contains_assertion(
        trace_of(LEGACY_TRANSCRIPT), "git add -A"
    )
    assert result.passed
    assert result.detail == "correctly absent"
