from __future__ import annotations

from shell_command_segment_scanning import (
    HEREDOC_OPENER_PATTERN,
    command_basename,
    segment_bounds_containing_offset,
    tokens_after_leading_variable_assignments,
)
from shell_heredoc_body import heredoc_body_bounds_after_opener
from shell_read_only_inspection_command import text_with_spans_blanked

SHELLS_READING_A_SCRIPT_FROM_STANDARD_INPUT = frozenset("bash dash ksh sh zsh".split())


def _opens_a_here_string(command_text, opener_start):
    return command_text[max(opener_start - 1, 0) : opener_start] == "<"


def _heredoc_feeds_a_shell(command_text, opener_start):
    owning_segment_start, _owning_segment_end = segment_bounds_containing_offset(
        command_text, opener_start
    )
    owning_tokens = tokens_after_leading_variable_assignments(
        command_text[owning_segment_start:opener_start]
    )
    return any(
        command_basename(token) in SHELLS_READING_A_SCRIPT_FROM_STANDARD_INPUT
        for token in owning_tokens
    )


def data_heredoc_body_bounds(command_text):
    data_body_bounds = []
    for opener_match in HEREDOC_OPENER_PATTERN.finditer(command_text):
        if _opens_a_here_string(command_text, opener_match.start()):
            continue
        if _heredoc_feeds_a_shell(command_text, opener_match.start()):
            continue
        body_bounds = heredoc_body_bounds_after_opener(
            command_text, opener_match.end(), opener_match.group(2)
        )
        if body_bounds is not None:
            data_body_bounds.append(body_bounds)
    return data_body_bounds


def shell_text_outside_data_heredoc_bodies(command_text):
    return text_with_spans_blanked(command_text, data_heredoc_body_bounds(command_text))
