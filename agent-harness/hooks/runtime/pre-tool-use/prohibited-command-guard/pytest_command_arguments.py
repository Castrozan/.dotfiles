from __future__ import annotations

import re

from shell_command_segment_scanning import (
    command_basename,
    quote_state_by_offset,
    segment_bounds_containing_offset,
)
from shell_read_only_inspection_command import (
    offset_lies_in_text_the_shell_never_runs,
)

PYTEST_COMMAND_WORD_PATTERN = re.compile(r"(?<![\w-])pytest\b", re.IGNORECASE)


def _pytest_word_offsets(command_text):
    normalized_characters = []
    source_offsets = []
    for offset, character in enumerate(command_text):
        if character in "\\'\"" or (
            character == "\n" and offset > 0 and command_text[offset - 1] == "\\"
        ):
            continue
        normalized_characters.append(character)
        source_offsets.append(offset)
    for match in PYTEST_COMMAND_WORD_PATTERN.finditer("".join(normalized_characters)):
        yield source_offsets[match.start()]


def _argument_vector(segment_text):
    import shlex

    lexer = shlex.shlex(segment_text, posix=True, punctuation_chars="<>")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return []


def _without_shell_redirections(argument_vector):
    argument_index = 0
    while argument_index < len(argument_vector):
        argument = argument_vector[argument_index]
        if (
            argument.isdecimal()
            and argument_index + 1 < len(argument_vector)
            and argument_vector[argument_index + 1].startswith(("<", ">"))
        ):
            argument_index += 1
            continue
        if argument.startswith(("<", ">")):
            argument_index += 2
            continue
        yield argument
        argument_index += 1


def _invocation_arguments_from_segment(segment_text):
    arguments = _argument_vector(segment_text)
    for argument_index, argument in enumerate(arguments):
        if command_basename(argument).lower() == "pytest":
            yield list(_without_shell_redirections(arguments[argument_index + 1 :]))
            return
    for argument in arguments:
        if len(argument) < len(segment_text) and PYTEST_COMMAND_WORD_PATTERN.search(
            argument
        ):
            yield from pytest_invocation_arguments(argument)


def pytest_invocation_arguments(command_text):
    quote_states = quote_state_by_offset(command_text)
    unquoted_structure = "".join(
        " " if quote_states[offset] else character
        for offset, character in enumerate(command_text)
    )
    inspected_segment_bounds = set()
    for command_offset in _pytest_word_offsets(command_text):
        if offset_lies_in_text_the_shell_never_runs(command_text, command_offset):
            continue
        segment_bounds = segment_bounds_containing_offset(
            unquoted_structure, command_offset
        )
        if segment_bounds in inspected_segment_bounds:
            continue
        inspected_segment_bounds.add(segment_bounds)
        segment_start, segment_end = segment_bounds
        yield from _invocation_arguments_from_segment(
            command_text[segment_start:segment_end]
        )
