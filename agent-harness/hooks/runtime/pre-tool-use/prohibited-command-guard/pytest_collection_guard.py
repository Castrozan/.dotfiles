from __future__ import annotations

import re

from ci_owned_command_patterns import (
    PYTEST_CI_OWNED_TIER_DENIAL_REASON,
    PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN,
    PYTEST_WHOLE_COLLECTION_DENIAL_REASON,
    PYTEST_WHOLE_TESTS_TREE_PATTERN,
)
from pytest_command_arguments import pytest_invocation_arguments

PYTEST_INFORMATION_OPTIONS = frozenset(
    {
        "-h",
        "--help",
        "-V",
        "--version",
        "--fixtures",
        "--funcargs",
        "--markers",
        "--cache-show",
    }
)
PYTEST_OPTIONS_WITH_AN_OPTIONAL_VALUE = frozenset({"--debug", "--cov"})
PYTEST_OPTIONS_REQUIRING_A_VALUE = frozenset(
    (
        "-k -m -c -p -o -r -W -n --maxfail --pdbcls --capture --lfnf "
        "--last-failed-no-failures --durations --durations-min --verbosity --tb "
        "--show-capture --color --code-highlight --pastebin --junit-xml --junitxml "
        "--junit-prefix --junitprefix --pythonwarnings --ignore --ignore-glob "
        "--deselect --confcutdir --import-mode --doctest-report --doctest-glob "
        "--config-file --rootdir --basetemp --override-ini --assert --log-level "
        "--log-format --log-date-format --log-cli-level --log-cli-format "
        "--log-cli-date-format --log-file --log-file-mode --log-file-level "
        "--log-file-format --log-file-date-format --log-auto-indent --log-disable "
        "--cov-report --cov-config --cov-fail-under --cov-precision "
        "--cov-context --numprocesses --maxprocesses --max-worker-restart --dist "
        "--tx --rsyncdir --rsyncignore"
    ).split()
)
PYTEST_SHORT_OPTIONS_TAKING_A_VALUE = frozenset(
    option[1:] for option in PYTEST_OPTIONS_REQUIRING_A_VALUE if len(option) == 2
)


def _option_takes_a_separate_value(argument, following_argument):
    if "=" in argument:
        return False
    if argument in PYTEST_OPTIONS_REQUIRING_A_VALUE:
        return True
    if argument in PYTEST_OPTIONS_WITH_AN_OPTIONAL_VALUE:
        return following_argument is not None and not following_argument.startswith("-")
    if argument.startswith("--"):
        return False
    for offset, character in enumerate(argument[1:], 1):
        if character in PYTEST_SHORT_OPTIONS_TAKING_A_VALUE:
            return offset == len(argument) - 1
    return False


def _collection_paths(argument_vector):
    arguments = argument_vector
    paths = []
    argument_index = 0
    while argument_index < len(arguments):
        argument = arguments[argument_index]
        if argument == "--":
            return paths + arguments[argument_index + 1 :]
        option = argument.partition("=")[0]
        if option in PYTEST_INFORMATION_OPTIONS:
            return None
        if argument.startswith("-"):
            following_argument = (
                arguments[argument_index + 1]
                if argument_index + 1 < len(arguments)
                else None
            )
            argument_index += (
                2 if _option_takes_a_separate_value(argument, following_argument) else 1
            )
            continue
        paths.append(argument)
        argument_index += 1
    return paths


def _collection_violation(argument_vector):
    paths = _collection_paths(argument_vector)
    if paths is None:
        return None
    for path in paths:
        if re.search(PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN, path, re.IGNORECASE):
            return (
                PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN,
                PYTEST_CI_OWNED_TIER_DENIAL_REASON,
            )
        if (
            path.rstrip("/") in {".", "./."}
            or path.rstrip("/").rsplit("/", 1)[-1] == "agents"
            or re.search(PYTEST_WHOLE_TESTS_TREE_PATTERN, path, re.IGNORECASE)
        ):
            return "pytest", PYTEST_WHOLE_COLLECTION_DENIAL_REASON
    if not paths:
        return "pytest", PYTEST_WHOLE_COLLECTION_DENIAL_REASON
    return None


def find_first_pytest_collection_violation(command_text):
    for arguments in pytest_invocation_arguments(command_text):
        violation = _collection_violation(arguments)
        if violation is not None:
            return violation
    return None
