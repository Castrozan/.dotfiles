from __future__ import annotations

from shell_command_segment_scanning import (
    leading_command_name,
    offset_after_leading_segment_separators,
    offset_is_inside_command_substitution,
    offset_separates_segments,
    pipeline_downstream_executes_its_input,
    quote_state_by_offset,
    segment_bounds_containing_offset,
    subcommand_after_global_options,
    tokens_after_leading_variable_assignments,
)
from shell_heredoc_body import (
    inert_heredoc_body_bounds,
    offset_lies_in_inert_heredoc_body,
)

READ_ONLY_INSPECTION_COMMANDS = frozenset(
    "ack basename bat cat cksum column comm cut date diff dirname du echo egrep "
    "fgrep file grep head hexdump jq less ls md5sum more nl od printf pwd readlink "
    "realpath rg seq shasum sort stat strings tail tr tree type uniq wc which yq".split()
)

READ_ONLY_INSPECTION_SUBCOMMANDS_BY_COMMAND = {
    "git": frozenset(
        "blame cat-file count-objects describe diff for-each-ref grep log ls-files "
        "ls-remote ls-tree rev-list rev-parse shortlog show show-ref status "
        "whatchanged".split()
    )
}

READ_ONLY_INSPECTION_FLAGS_BY_COMMAND = {"command": frozenset({"-v", "-V"})}


def segment_is_read_only_inspection(segment_text):
    tokens = tokens_after_leading_variable_assignments(segment_text)
    command_name = leading_command_name(tokens)
    if not command_name:
        return False
    if command_name in READ_ONLY_INSPECTION_COMMANDS:
        return True
    allowed_subcommands = READ_ONLY_INSPECTION_SUBCOMMANDS_BY_COMMAND.get(command_name)
    if allowed_subcommands is not None:
        return subcommand_after_global_options(tokens[1:]) in allowed_subcommands
    allowed_flags = READ_ONLY_INSPECTION_FLAGS_BY_COMMAND.get(command_name)
    if allowed_flags is not None:
        return len(tokens) > 1 and tokens[1] in allowed_flags
    return False


def offset_lies_in_read_only_inspection_command_segment(command_text, offset):
    inspected_offset = offset_after_leading_segment_separators(command_text, offset)
    if offset_is_inside_command_substitution(command_text, inspected_offset):
        return False
    segment_start, segment_end = segment_bounds_containing_offset(
        command_text, inspected_offset
    )
    if not segment_is_read_only_inspection(command_text[segment_start:segment_end]):
        return False
    return not pipeline_downstream_executes_its_input(command_text, segment_end)


def offset_lies_in_text_the_shell_never_runs(command_text, offset):
    inspected_offset = offset_after_leading_segment_separators(command_text, offset)
    if offset_lies_in_inert_heredoc_body(command_text, inspected_offset):
        return True
    return offset_lies_in_read_only_inspection_command_segment(command_text, offset)


def read_only_segment_bounds(command_text):
    quote_states = quote_state_by_offset(command_text)
    inert_bounds = []
    segment_start = 0
    for offset in range(len(command_text) + 1):
        ends_the_segment = offset == len(command_text) or offset_separates_segments(
            command_text, offset, quote_states
        )
        if not ends_the_segment:
            continue
        segment_is_inert = not offset_is_inside_command_substitution(
            command_text, segment_start
        ) and segment_is_read_only_inspection(command_text[segment_start:offset])
        if segment_is_inert and not pipeline_downstream_executes_its_input(
            command_text, offset
        ):
            inert_bounds.append((segment_start, offset))
        segment_start = offset + 1
    return inert_bounds


def text_with_spans_blanked(command_text, spans):
    if not spans:
        return command_text
    remaining_characters = list(command_text)
    for span_start, span_end in spans:
        for offset in range(span_start, min(span_end, len(command_text))):
            if not remaining_characters[offset].isspace():
                remaining_characters[offset] = " "
    return "".join(remaining_characters)


def command_text_outside_inert_heredoc_bodies(command_text):
    return text_with_spans_blanked(
        command_text, inert_heredoc_body_bounds(command_text)
    )


def command_text_the_shell_executes(command_text):
    return text_with_spans_blanked(
        command_text,
        inert_heredoc_body_bounds(command_text)
        + read_only_segment_bounds(command_text),
    )
