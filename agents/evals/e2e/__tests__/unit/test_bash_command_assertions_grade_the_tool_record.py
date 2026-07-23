from e2e_assertions_skills_tools import (
    check_bash_command_contains_assertion,
    check_bash_command_not_contains_assertion,
)
from e2e_models import TerminalSessionTrace

PROSE_MENTIONING_FIND = (
    "● I'll find all the Python files for you.\n"
    "● Grep(pattern: **/*.py)\n"
    "● There are 5 Python files.\n"
)


def trace_with(bash_commands, raw_output):
    return TerminalSessionTrace(
        raw_terminal_output=raw_output,
        detected_bash_commands=list(bash_commands),
        duration_seconds=1.0,
        timed_out=False,
    )


def test_prose_naming_a_forbidden_command_is_not_treated_as_running_it():
    result = check_bash_command_not_contains_assertion(
        trace_with([], PROSE_MENTIONING_FIND), "find "
    )
    assert result.passed, (
        "the agent used Grep and only said the word find, so grading the whole "
        f"terminal instead of the Bash calls fails a correct run: {result.detail}"
    )


def test_a_forbidden_command_that_was_actually_run_still_fails():
    result = check_bash_command_not_contains_assertion(
        trace_with(["find . -name '*.py'"], PROSE_MENTIONING_FIND), "find "
    )
    assert not result.passed
    assert "find ." in result.detail, (
        "the failure has to name the command that was run, or nobody can tell which "
        "call tripped it"
    )


def test_a_required_command_is_not_satisfied_by_prose_alone():
    result = check_bash_command_contains_assertion(
        trace_with([], "● I would run git status here.\n"), "git status"
    )
    assert not result.passed, (
        "an agent that only talks about running a command has not run it, and "
        "passing on the mention grades vocabulary instead of behaviour"
    )


def test_a_required_command_passes_when_the_bash_call_is_recorded():
    result = check_bash_command_contains_assertion(
        trace_with(["git status --short"], ""), "git status"
    )
    assert result.passed
    assert "git status --short" in result.detail
