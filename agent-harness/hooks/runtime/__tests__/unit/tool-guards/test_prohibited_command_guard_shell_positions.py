from functools import reduce
from itertools import product

import prohibited_command_guard_handler
from hypothesis import example, given
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

SINGLE_OPTION_CHOICES = ((),) + tuple((option,) for option in PYTEST_OPTIONS)

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


def commands_the_guard_allows(shell_commands):
    return [command for command in shell_commands if guard_decision(command) != "deny"]


def test_every_banned_command_is_denied_alone_and_in_each_shell_position():
    commands = BANNED_COMMANDS + tuple(
        whole_collection_pytest_command(runner, (), target, ())
        for runner, target in product(PYTEST_RUNNERS, WHOLE_COLLECTION_TARGETS)
    )

    assert (
        commands_the_guard_allows(
            placed_in_shell_positions(command, positions)
            for command in commands
            for positions in ((), *((position,) for position in SHELL_POSITIONS))
        )
        == []
    )


def test_every_whole_collection_pytest_run_is_denied_with_one_option_on_either_side():
    assert (
        commands_the_guard_allows(
            whole_collection_pytest_command(runner, before, target, after)
            for runner, before, target, after in product(
                PYTEST_RUNNERS,
                SINGLE_OPTION_CHOICES,
                WHOLE_COLLECTION_TARGETS,
                SINGLE_OPTION_CHOICES,
            )
        )
        == []
    )


@given(command=st.sampled_from(BANNED_COMMANDS), positions=shell_positions)
def test_a_banned_command_is_denied_in_nested_shell_positions(command, positions):
    assert guard_decision(placed_in_shell_positions(command, positions)) == "deny"


@given(
    runner=st.sampled_from(PYTEST_RUNNERS),
    options_before=st.lists(st.sampled_from(PYTEST_OPTIONS), max_size=2),
    target=st.sampled_from(WHOLE_COLLECTION_TARGETS),
    options_after=st.lists(st.sampled_from(PYTEST_OPTIONS), max_size=2),
    positions=shell_positions,
)
@example(
    runner="pytest",
    options_before=["-q", "-n auto"],
    target="",
    options_after=[],
    positions=[],
)
def test_a_whole_collection_pytest_run_is_denied_with_any_options_in_any_position(
    runner, options_before, target, options_after, positions
):
    command = whole_collection_pytest_command(
        runner, options_before, target, options_after
    )

    assert guard_decision(placed_in_shell_positions(command, positions)) == "deny"
