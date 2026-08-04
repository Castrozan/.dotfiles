from __future__ import annotations

SHELL_SEGMENT_SEPARATOR_CHARACTERS = frozenset(";\n|&()`")

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

GLOBAL_OPTIONS_TAKING_A_SEPARATE_VALUE = frozenset(
    "-C -c --exec-path --git-dir --namespace --work-tree".split()
)

INTERPRETER_COMMANDS_EXECUTING_PIPED_INPUT = frozenset(
    "bash bun dash deno entr env eval fish ksh nix-shell node parallel perl python "
    "python2 python3 ruby sh source xargs zsh".split()
)


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
    return tokens[0].rsplit("/", 1)[-1]


def subcommand_after_global_options(tokens):
    token_index = 0
    while token_index < len(tokens):
        token = tokens[token_index]
        if not token.startswith("-"):
            return token
        token_index += 2 if token in GLOBAL_OPTIONS_TAKING_A_SEPARATE_VALUE else 1
    return ""


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


def offset_after_leading_segment_separators(command_text, offset):
    while offset < len(command_text) and (
        command_text[offset] in SHELL_SEGMENT_SEPARATOR_CHARACTERS
        or command_text[offset].isspace()
    ):
        offset += 1
    return offset


def segment_bounds_containing_offset(command_text, offset):
    segment_start = 0
    scan_index = offset - 1
    while scan_index >= 0:
        if command_text[scan_index] in SHELL_SEGMENT_SEPARATOR_CHARACTERS:
            segment_start = scan_index + 1
            break
        scan_index -= 1
    segment_end = len(command_text)
    scan_index = offset
    while scan_index < len(command_text):
        if command_text[scan_index] in SHELL_SEGMENT_SEPARATOR_CHARACTERS:
            segment_end = scan_index
            break
        scan_index += 1
    return segment_start, segment_end


def offset_is_inside_command_substitution(command_text, offset):
    text_before_offset = command_text[:offset]
    if text_before_offset.count("`") % 2 == 1:
        return True
    return text_before_offset.count("(") > text_before_offset.count(")")


def pipeline_downstream_executes_its_input(command_text, segment_end):
    scan_index = segment_end
    while scan_index < len(command_text) and command_text[scan_index] == "|":
        if command_text.startswith("||", scan_index):
            return False
        downstream_start = scan_index + 1
        downstream_end = downstream_start
        while (
            downstream_end < len(command_text)
            and command_text[downstream_end] not in SHELL_SEGMENT_SEPARATOR_CHARACTERS
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
