from __future__ import annotations

COMMAND_SUBSTITUTION_OPENER = "$("
BACKTICK = "`"
SHELL_KEYWORDS_BEFORE_A_COMMAND = frozenset(
    "{ ! if then else elif do while until time".split()
)
OPERAND_COUNT_BY_COMMAND_WRAPPER = {
    "command": 0,
    "env": 0,
    "exec": 0,
    "nice": 0,
    "nohup": 0,
    "proxy": 0,
    "rtk": 0,
    "sudo": 0,
    "timeout": 1,
}


class _SimpleCommandBuilder:
    def __init__(self, simple_commands):
        self.simple_commands = simple_commands
        self.words = []
        self.word_fragments = []
        self.word_is_open = False

    def extend_word(self, fragment):
        self.word_fragments.append(fragment)
        self.word_is_open = True

    def close_word(self):
        if self.word_is_open:
            self.words.append("".join(self.word_fragments))
        self.word_fragments = []
        self.word_is_open = False

    def close_command(self):
        self.close_word()
        if self.words:
            self.simple_commands.append(self.words)
        self.words = []


def _offset_after_plain_character(command_text, offset, builder):
    builder.extend_word(command_text[offset])
    return offset + 1


def _offset_after_escape(command_text, offset, builder):
    escaped_character = command_text[offset + 1 : offset + 2]
    if escaped_character != "\n":
        builder.extend_word(escaped_character)
    return offset + 2


def _offset_after_single_quoted(command_text, offset, builder):
    closing_offset = command_text.find("'", offset + 1)
    if closing_offset == -1:
        closing_offset = len(command_text)
    builder.extend_word(command_text[offset + 1 : closing_offset])
    return closing_offset + 1


def _offset_after_double_quoted(command_text, offset, builder):
    builder.extend_word("")
    offset += 1
    while offset < len(command_text) and command_text[offset] != '"':
        scan_lexeme = DOUBLE_QUOTED_LEXEME_SCANNERS_BY_CHARACTER.get(
            command_text[offset], _offset_after_plain_character
        )
        offset = scan_lexeme(command_text, offset, builder)
    return offset + 1


def _offset_after_backtick_substitution(command_text, offset, builder):
    builder.extend_word("")
    return _offset_after_commands(
        command_text, offset + 1, BACKTICK, builder.simple_commands
    )


def _offset_after_dollar(command_text, offset, builder):
    if not command_text.startswith(COMMAND_SUBSTITUTION_OPENER, offset):
        return _offset_after_plain_character(command_text, offset, builder)
    builder.extend_word("")
    return _offset_after_commands(
        command_text, offset + 2, ")", builder.simple_commands
    )


def _offset_after_comment_marker(command_text, offset, builder):
    if builder.word_is_open:
        return _offset_after_plain_character(command_text, offset, builder)
    line_end = command_text.find("\n", offset)
    return len(command_text) if line_end == -1 else line_end


def _offset_after_subshell(command_text, offset, builder):
    builder.close_command()
    return _offset_after_commands(
        command_text, offset + 1, ")", builder.simple_commands
    )


def _offset_after_command_separator(_command_text, offset, builder):
    builder.close_command()
    return offset + 1


def _offset_after_ampersand(command_text, offset, builder):
    belongs_to_a_redirection = ">" in (
        command_text[max(offset - 1, 0) : offset],
        command_text[offset + 1 : offset + 2],
    )
    if belongs_to_a_redirection:
        return _offset_after_plain_character(command_text, offset, builder)
    return _offset_after_command_separator(command_text, offset, builder)


def _offset_after_word_separator(_command_text, offset, builder):
    builder.close_word()
    return offset + 1


DOUBLE_QUOTED_LEXEME_SCANNERS_BY_CHARACTER = {
    "\\": _offset_after_escape,
    "$": _offset_after_dollar,
    BACKTICK: _offset_after_backtick_substitution,
}

LEXEME_SCANNERS_BY_CHARACTER = {
    **DOUBLE_QUOTED_LEXEME_SCANNERS_BY_CHARACTER,
    "'": _offset_after_single_quoted,
    '"': _offset_after_double_quoted,
    "#": _offset_after_comment_marker,
    "(": _offset_after_subshell,
    ")": _offset_after_command_separator,
    ";": _offset_after_command_separator,
    "\n": _offset_after_command_separator,
    "|": _offset_after_command_separator,
    "&": _offset_after_ampersand,
    **dict.fromkeys(" \t\r\f\v", _offset_after_word_separator),
}


def _offset_after_commands(command_text, offset, closing_character, simple_commands):
    builder = _SimpleCommandBuilder(simple_commands)
    while offset < len(command_text):
        character = command_text[offset]
        if character == closing_character:
            builder.close_command()
            return offset + 1
        scan_lexeme = LEXEME_SCANNERS_BY_CHARACTER.get(
            character, _offset_after_plain_character
        )
        offset = scan_lexeme(command_text, offset, builder)
    builder.close_command()
    return offset


def simple_commands_in(command_text):
    simple_commands = []
    _offset_after_commands(command_text, 0, "", simple_commands)
    return simple_commands


def _is_variable_assignment(word):
    assigned_name, assignment_separator, _assigned_value = word.partition("=")
    return bool(assignment_separator) and assigned_name.isidentifier()


def _precedes_the_command(word):
    return _is_variable_assignment(word) or word in SHELL_KEYWORDS_BEFORE_A_COMMAND


def _words_after_wrapper_options(words):
    option_count = 0
    while option_count < len(words) and words[option_count].startswith("-"):
        option_count += 1
    return words[option_count:]


def words_after_command_wrappers(words):
    remaining_words = list(words)
    while remaining_words:
        leading_word = remaining_words[0]
        if _precedes_the_command(leading_word):
            remaining_words = remaining_words[1:]
            continue
        operand_count = OPERAND_COUNT_BY_COMMAND_WRAPPER.get(
            leading_word.rsplit("/", 1)[-1]
        )
        if operand_count is None:
            break
        remaining_words = _words_after_wrapper_options(remaining_words[1:])[
            operand_count:
        ]
    return remaining_words
