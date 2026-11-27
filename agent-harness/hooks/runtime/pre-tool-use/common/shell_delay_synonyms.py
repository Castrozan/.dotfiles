from __future__ import annotations

import re

from shell_delay_durations import KEEP_ALIVE_DURATIONS

SLEEP_COMMAND_NAMES = frozenset({"sleep", "gsleep"})
TAIL_FOLLOW_OPTIONS = frozenset({"-f", "-F", "--follow"})
FILE_NOTHING_IS_WRITTEN_TO = "/dev/null"
READ_TIMEOUT_OPTION_PATTERN = re.compile(r"-[a-zA-Z]*t(.*)")
DISCARDED_READ_VARIABLE = "_"


def command_blocks_until_killed(command_words):
    if not command_words:
        return False
    command_name = command_words[0].rsplit("/", 1)[-1]
    arguments = command_words[1:]
    if command_name in SLEEP_COMMAND_NAMES:
        return bool(KEEP_ALIVE_DURATIONS.intersection(arguments))
    return (
        command_name == "tail"
        and bool(TAIL_FOLLOW_OPTIONS.intersection(arguments))
        and FILE_NOTHING_IS_WRITTEN_TO in arguments
    )


def _read_timeout_word(read_arguments):
    for argument_index, argument in enumerate(read_arguments):
        timeout_option = READ_TIMEOUT_OPTION_PATTERN.fullmatch(argument)
        if timeout_option is None:
            continue
        following_words = read_arguments[argument_index + 1 : argument_index + 2]
        return timeout_option.group(1) or "".join(following_words)
    return None


def _read_discards_its_input(read_arguments):
    reads_the_file_nothing_is_written_to = "<" + FILE_NOTHING_IS_WRITTEN_TO in "".join(
        read_arguments
    )
    return DISCARDED_READ_VARIABLE in read_arguments or (
        reads_the_file_nothing_is_written_to
    )


def timeout_word_of_a_read_that_only_passes_time(read_arguments):
    if not _read_discards_its_input(read_arguments):
        return None
    return _read_timeout_word(read_arguments)
