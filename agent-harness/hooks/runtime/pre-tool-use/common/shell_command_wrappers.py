from __future__ import annotations

from collections import namedtuple

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
TIMEOUT_WRAPPER_NAME = "timeout"
LOOKUP_ONLY_OPTION_LETTERS_BY_WRAPPER = {"command": frozenset("vV")}

WrappedCommand = namedtuple("WrappedCommand", "command_words timeout_duration_word")


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


def _timeout_duration_word(wrapper_name, operands_and_command):
    if wrapper_name != TIMEOUT_WRAPPER_NAME:
        return None
    return "".join(operands_and_command[:1]) or None


def _only_looks_up_the_command(wrapper_name, option_words):
    lookup_letters = LOOKUP_ONLY_OPTION_LETTERS_BY_WRAPPER.get(
        wrapper_name, frozenset()
    )
    return any(lookup_letters.intersection(option) for option in option_words)


def _words_after_one_wrapper(words):
    if _precedes_the_command(words[0]):
        return words[1:], None
    wrapper_name = words[0].rsplit("/", 1)[-1]
    operand_count = OPERAND_COUNT_BY_COMMAND_WRAPPER.get(wrapper_name)
    if operand_count is None:
        return None
    operands_and_command = _words_after_wrapper_options(words[1:])
    option_words = words[1 : len(words) - len(operands_and_command)]
    if _only_looks_up_the_command(wrapper_name, option_words):
        return None
    return (
        operands_and_command[operand_count:],
        _timeout_duration_word(wrapper_name, operands_and_command),
    )


def command_inside_wrappers(words):
    remaining_words = list(words)
    timeout_duration_words = []
    while remaining_words:
        unwrapped = _words_after_one_wrapper(remaining_words)
        if unwrapped is None:
            break
        remaining_words, timeout_duration_word = unwrapped
        timeout_duration_words.append(timeout_duration_word)
    outermost_timeout_words = list(filter(None, timeout_duration_words))[:1]
    return WrappedCommand(remaining_words, "".join(outermost_timeout_words) or None)


def words_after_command_wrappers(words):
    return command_inside_wrappers(words).command_words
