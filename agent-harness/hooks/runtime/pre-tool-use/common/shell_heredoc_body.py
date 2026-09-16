from __future__ import annotations

from shell_command_segment_scanning import (
    HEREDOC_OPENER_PATTERN,
    INTERPRETER_COMMANDS_EXECUTING_PIPED_INPUT,
    command_basename,
    pipeline_downstream_executes_its_input,
    segment_bounds_containing_offset,
    tokens_after_leading_variable_assignments,
)


def heredoc_body_bounds_after_opener(command_text, opener_end, delimiter):
    body_start = command_text.find("\n", opener_end)
    if body_start == -1:
        return None
    body_start += 1
    scan_index = body_start
    while scan_index < len(command_text):
        line_end = command_text.find("\n", scan_index)
        if line_end == -1:
            line_end = len(command_text)
        if command_text[scan_index:line_end].strip() == delimiter:
            return body_start, scan_index
        scan_index = line_end + 1
    return body_start, len(command_text)


def heredoc_owner_executes_its_body(command_text, opener_start):
    owning_segment_start, segment_end = segment_bounds_containing_offset(
        command_text, opener_start
    )
    owning_tokens = tokens_after_leading_variable_assignments(
        command_text[owning_segment_start:opener_start]
    )
    if any(
        command_basename(token) in INTERPRETER_COMMANDS_EXECUTING_PIPED_INPUT
        for token in owning_tokens
    ):
        return True
    return pipeline_downstream_executes_its_input(command_text, segment_end)


def inert_heredoc_body_bounds(command_text):
    inert_bounds = []
    for opener_match in HEREDOC_OPENER_PATTERN.finditer(command_text):
        if heredoc_owner_executes_its_body(command_text, opener_match.start()):
            continue
        body_bounds = heredoc_body_bounds_after_opener(
            command_text, opener_match.end(), opener_match.group(2)
        )
        if body_bounds is not None:
            inert_bounds.append(body_bounds)
    return inert_bounds


def offset_lies_in_inert_heredoc_body(command_text, offset):
    return any(
        body_start <= offset < body_end
        for body_start, body_end in inert_heredoc_body_bounds(command_text)
    )
