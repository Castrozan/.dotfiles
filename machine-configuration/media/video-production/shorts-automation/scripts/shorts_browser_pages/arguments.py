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
    position = 0
    while position < len(arguments):
        value = arguments[position]
        if value == "--":
            remaining.extend(arguments[position:])
            break
        if value in TAB_VALUE_FLAGS:
            remaining.extend(arguments[position : position + 2])
            position += 2
            continue
        if value == "--tab":
            position += 1
            if position == len(arguments):
                raise ValueError("A tab ID is required")
            selected = arguments[position]
        elif value.startswith("--tab="):
            selected = value.split("=", 1)[1]
        else:
            remaining.append(value)
            position += 1
            continue
        if identifier is not None or not selected:
            raise ValueError("Exactly one tab ID is required")
        identifier = selected
        position += 1
    return remaining, identifier


def positional_tab_arguments(arguments):
    prefix = (
        2
        if arguments[0] == "tab"
        and len(arguments) > 1
        and arguments[1] in POSITIONAL_TAB_COMMANDS
        else 1
    )
    position = prefix
    while position < len(arguments):
        value = arguments[position]
        if value == "--":
            position += 1
            break
        if not value.startswith("-"):
            break
        position += 2 if value in TAB_VALUE_FLAGS else 1
    options = arguments[prefix:]
    identifier = None
    if position < len(arguments):
        identifier = options.pop(position - prefix)
    return PositionalTabArguments(arguments[:prefix], options, identifier)
