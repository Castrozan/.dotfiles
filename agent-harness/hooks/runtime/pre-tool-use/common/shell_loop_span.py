from __future__ import annotations

import re

from shell_command_segment_scanning import UNQUOTED_STATE, quote_state_by_offset

SHELL_LOOP_KEYWORD_PATTERN = re.compile(
    r"(?:^|[;&|({\n]|\b(?:do|then|else)\s)\s*(until|while|for)(?=\s)"
)
SHELL_LOOP_BODY_OPENER_PATTERN = re.compile(r"[;\n]\s*do(?=\s|$)")
SHELL_LOOP_CLOSER_PATTERN = re.compile(r"(?<![\w-])done(?![\w-])")


def shell_loop_span(command_string):
    quote_states = quote_state_by_offset(command_string)
    unquoted_loop_keyword_offsets = [
        loop_keyword.start(1)
        for loop_keyword in SHELL_LOOP_KEYWORD_PATTERN.finditer(command_string)
        if quote_states[loop_keyword.start(1)] == UNQUOTED_STATE
    ]
    if not unquoted_loop_keyword_offsets:
        return None
    loop_start = unquoted_loop_keyword_offsets[0]
    if not SHELL_LOOP_BODY_OPENER_PATTERN.search(command_string, loop_start):
        return None
    loop_closers = list(SHELL_LOOP_CLOSER_PATTERN.finditer(command_string, loop_start))
    loop_end = loop_closers[-1].end() if loop_closers else len(command_string)
    return loop_start, loop_end


def pattern_matches_inside_a_shell_loop(pattern, command_string):
    loop_span = shell_loop_span(command_string)
    if loop_span is None:
        return False
    loop_start, loop_end = loop_span
    return bool(pattern.search(command_string, loop_start, loop_end))
