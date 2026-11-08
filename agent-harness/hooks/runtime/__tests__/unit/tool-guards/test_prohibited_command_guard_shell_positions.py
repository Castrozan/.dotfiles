from functools import reduce

import prohibited_command_guard_handler
from hypothesis import given
from hypothesis import strategies as st

BANNED_COMMANDS = (
    "git add -A",
    "git add --all",
    "git add .",
    "nix flake check",
    "launchctl submit -l example -- /bin/true",
)

PYTEST_RUNNERS = ("pytest", "python3 -m pytest")

WHOLE_COLLECTION_TARGETS = (
    "",
    ".",
    "./",
    "agents",
    "agents/",
    "./agents",
    "agent-harness/quality/evaluations",
    "agent-harness/quality/evaluations/",
    "agent-harness/quality/evaluations/__tests__/unit",
    "agent-harness/quality/evaluations/__tests__/unit/",
    "agent-harness/hooks/runtime/__tests__/unit",
)

PYTEST_OPTIONS = ("-q", "-x", "-v", "--tb=short", "-n auto")

SHELL_POSITIONS = (
    "   {}",
    "\t{}",
    "echo one\n{}",
    "sudo {}",
    "$({})",
    "`{}`",
    "if true; then {}; fi",
    "for f in a; do {}; done",
    "nohup {}",
    "env FOO=1 {}",
    "FOO=1 {}",
    "echo hi; {}",
    "cd /tmp && {}",
    "true | {}",
    "{} && echo done",
    "{}; echo done",
    "bash -lc '{}'",
    'sh -c "{}"',
    "( {} )",
    "{{ {}; }}",
    "time {}",
    "command {}",
    "exec {}",
    "nice {}",
    "timeout 60 {}",
    "xargs {}",
)

shell_positions = st.lists(st.sampled_from(SHELL_POSITIONS), max_size=3)


def placed_in_shell_positions(command, positions):
    return reduce(lambda placed, position: position.format(placed), positions, command)


def whole_collection_pytest_command(runner, options_before, target, options_after):
    return " ".join(
        word for word in (runner, *options_before, target, *options_after) if word
    )


def guard_decision(shell_command):
    result = prohibited_command_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": shell_command}}
    )
    return None if result is None else result.decision


@given(command=st.sampled_from(BANNED_COMMANDS), positions=shell_positions)
def test_a_banned_command_is_denied_in_every_shell_position(command, positions):
    assert guard_decision(placed_in_shell_positions(command, positions)) == "deny"


@given(
    runner=st.sampled_from(PYTEST_RUNNERS),
    options_before=st.lists(st.sampled_from(PYTEST_OPTIONS), max_size=2),
    target=st.sampled_from(WHOLE_COLLECTION_TARGETS),
    options_after=st.lists(st.sampled_from(PYTEST_OPTIONS), max_size=2),
    positions=shell_positions,
)
def test_a_whole_collection_pytest_run_is_denied_with_any_options_in_any_position(
    runner, options_before, target, options_after, positions
):
    command = whole_collection_pytest_command(
        runner, options_before, target, options_after
    )

    assert guard_decision(placed_in_shell_positions(command, positions)) == "deny"
