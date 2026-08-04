from __future__ import annotations

import re

SHELL_SEGMENT_SEPARATOR_CHARACTERS = frozenset(";\n|&()`")

SHELL_QUOTE_CHARACTERS = frozenset("'\"")

SHELL_SUBSTITUTION_CHARACTERS = frozenset("()`")

UNQUOTED_STATE = ""

LITERAL_QUOTE_CHARACTER = "'"

GLOBAL_OPTIONS_TAKING_A_SEPARATE_VALUE = frozenset(
    "-C -c --exec-path --git-dir --namespace --work-tree".split()
)

INTERPRETER_COMMANDS_EXECUTING_PIPED_INPUT = frozenset(
    "bash bun dash deno entr env eval fish ksh nix-shell node parallel perl python "
    "python2 python3 ruby sh source xargs zsh".split()
)

HEREDOC_OPENER_PATTERN = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def command_basename(token):
    return token.rsplit("/", 1)[-1]


def tokens_after_leading_variable_assignments(segment_text):
    tokens = segment_text.split()
    first_command_token_index = 0
    while first_command_token_index < len(tokens):
        assigned_name, assignment_separator, _assigned_value = tokens[
            first_command_token_index
        ].partition("=")
        if not assignment_separator or not assigned_name.isidentifier():
            break
        first_command_token_index += 1
    return tokens[first_command_token_index:]


def leading_command_name(tokens):
    if not tokens:
        return ""
    return command_basename(tokens[0])


def subcommand_after_global_options(tokens):
    token_index = 0
    while token_index < len(tokens):
        token = tokens[token_index]
        if not token.startswith("-"):
            return token
        token_index += 2 if token in GLOBAL_OPTIONS_TAKING_A_SEPARATE_VALUE else 1
    return ""


def quote_state_by_offset(command_text):
    quote_states = [UNQUOTED_STATE] * len(command_text)
    open_quote_character = UNQUOTED_STATE
    scan_index = 0
    while scan_index < len(command_text):
        character = command_text[scan_index]
        if character == "\\" and open_quote_character != LITERAL_QUOTE_CHARACTER:
            quote_states[scan_index] = LITERAL_QUOTE_CHARACTER
            if scan_index + 1 < len(command_text):
                quote_states[scan_index + 1] = LITERAL_QUOTE_CHARACTER
            scan_index += 2
            continue
        if open_quote_character:
            quote_states[scan_index] = open_quote_character
            if character == open_quote_character:
                open_quote_character = UNQUOTED_STATE
        elif character in SHELL_QUOTE_CHARACTERS:
            quote_states[scan_index] = character
            open_quote_character = character
        scan_index += 1
    return quote_states


def offset_separates_segments(command_text, offset, quote_states=None):
    character = command_text[offset]
    if character not in SHELL_SEGMENT_SEPARATOR_CHARACTERS:
        return False
    if quote_states is None:
        quote_states = quote_state_by_offset(command_text)
    quote_state = quote_states[offset]
    if quote_state == UNQUOTED_STATE:
        return True
    if quote_state == LITERAL_QUOTE_CHARACTER:
        return False
    return character in SHELL_SUBSTITUTION_CHARACTERS


def offset_after_leading_segment_separators(command_text, offset):
    quote_states = quote_state_by_offset(command_text)
    while offset < len(command_text) and (
        offset_separates_segments(command_text, offset, quote_states)
        or command_text[offset].isspace()
    ):
        offset += 1
    return offset


def segment_bounds_containing_offset(command_text, offset):
    quote_states = quote_state_by_offset(command_text)
    segment_start = 0
    scan_index = offset - 1
    while scan_index >= 0:
        if offset_separates_segments(command_text, scan_index, quote_states):
            segment_start = scan_index + 1
            break
        scan_index -= 1
    segment_end = len(command_text)
    scan_index = offset
    while scan_index < len(command_text):
        if offset_separates_segments(command_text, scan_index, quote_states):
            segment_end = scan_index
            break
        scan_index += 1
    return segment_start, segment_end


def offset_is_inside_command_substitution(command_text, offset):
    quote_states = quote_state_by_offset(command_text)
    substitution_characters_in_force = [
        character
        for character_offset, character in enumerate(command_text[:offset])
        if quote_states[character_offset] != LITERAL_QUOTE_CHARACTER
    ]
    if substitution_characters_in_force.count("`") % 2 == 1:
        return True
    return substitution_characters_in_force.count(
        "("
    ) > substitution_characters_in_force.count(")")


def pipeline_downstream_executes_its_input(command_text, segment_end):
    quote_states = quote_state_by_offset(command_text)
    scan_index = segment_end
    while scan_index < len(command_text) and command_text[scan_index] == "|":
        if command_text.startswith("||", scan_index):
            return False
        downstream_start = scan_index + 1
        downstream_end = downstream_start
        while downstream_end < len(command_text) and not offset_separates_segments(
            command_text, downstream_end, quote_states
        ):
            downstream_end += 1
        downstream_command_name = leading_command_name(
            tokens_after_leading_variable_assignments(
                command_text[downstream_start:downstream_end]
            )
        )
        if downstream_command_name in INTERPRETER_COMMANDS_EXECUTING_PIPED_INPUT:
            return True
        scan_index = downstream_end
    return False
