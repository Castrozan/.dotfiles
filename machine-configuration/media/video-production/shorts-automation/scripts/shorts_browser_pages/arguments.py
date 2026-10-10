from itertools import islice
from typing import NamedTuple


POSITIONAL_TAB_COMMANDS = frozenset({"close", "handoff", "handoff-status", "resume"})
TAB_VALUE_FLAGS = frozenset({"--reason", "--timeout-ms", "--status"})


class PositionalTabArguments(NamedTuple):
    command: list[str]
    options: list[str]
    identifier: str | None


def tab_arguments(arguments):
    remaining = []
    identifier = None
    values = iter(arguments)
    for value in values:
        if value == "--":
            remaining.extend([value, *values])
            break
        if value in TAB_VALUE_FLAGS:
            remaining.extend([value, *islice(values, 1)])
            continue
        selected = named_tab_identifier(value, values)
        if selected is None:
            remaining.append(value)
            continue
        identifier = unique_tab_identifier(identifier, selected)
    return remaining, identifier


def named_tab_identifier(value, values):
    if value == "--tab":
        selected = next(values, None)
        if selected is None:
            raise ValueError("A tab ID is required")
        return selected
    if value.startswith("--tab="):
        return value.split("=", 1)[1]
    return None


def unique_tab_identifier(previous, selected):
    if previous is not None or not selected:
        raise ValueError("Exactly one tab ID is required")
    return selected


def positional_command_length(arguments):
    if arguments[0] != "tab":
        return 1
    if len(arguments) > 1 and arguments[1] in POSITIONAL_TAB_COMMANDS:
        return 2
    return 1


def positional_tab_position(arguments, prefix):
    position = prefix
    while position < len(arguments):
        value = arguments[position]
        if value == "--":
            return position + 1
        if not value.startswith("-"):
            return position
        position += option_length(value)
    return position


def option_length(value):
    return 2 if value in TAB_VALUE_FLAGS else 1


def positional_tab_arguments(arguments):
    prefix = positional_command_length(arguments)
    position = positional_tab_position(arguments, prefix)
    options = arguments[prefix:]
    identifier = None
    if position < len(arguments):
        identifier = options.pop(position - prefix)
    return PositionalTabArguments(arguments[:prefix], options, identifier)
