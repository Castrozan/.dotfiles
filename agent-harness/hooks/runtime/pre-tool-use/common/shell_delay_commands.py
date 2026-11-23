from __future__ import annotations

import re

from shell_delay_durations import (
    duration_word_seconds,
    inline_program_after_option,
    python_program_sleep_durations,
    python_program_sleep_seconds,
    sleep_is_a_delay,
    sleep_seconds,
)
from shell_simple_commands import simple_commands_in, words_after_command_wrappers

CONDITION_LOOP_KEYWORDS = frozenset({"while", "until"})
ITERATION_LOOP_KEYWORDS = frozenset({"for", "select"})
LOOP_CLOSING_KEYWORD = "done"
LOOP_EXIT_COMMANDS = frozenset({"break", "exit", "return"})
KEYWORDS_BEFORE_A_LOOP = frozenset({"do", "then", "else", "elif", "if", "{", "!"})
SHELL_INTERPRETERS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})
PYTHON_INTERPRETER_PATTERN = re.compile(r"python(?:3(?:\.\d+)?)?")
COUNTER_ITEM_PATTERN = re.compile(r"^$|\.\.")
WATCH_DEFAULT_INTERVAL_SECONDS = 2.0
PACING_CEILING_SECONDS = 1.0


class ShellLoop:
    def __init__(self, polls):
        self.polls = polls


class ShellDelay:
    def __init__(self, seconds, loop):
        self.seconds = seconds
        self.loop = loop

    @property
    def paces_input(self):
        if self.seconds is None or self.seconds >= PACING_CEILING_SECONDS:
            return False
        return self.loop is None or not self.loop.polls


class _DelayScan:
    def __init__(self, enclosing_loop):
        self.open_loops = [enclosing_loop] if enclosing_loop else []
        self.inherited_loop_count = len(self.open_loops)
        self.delays = []

    def innermost_loop(self):
        return self.open_loops[-1] if self.open_loops else None

    def read_simple_command(self, words):
        words = _words_after_leading_keywords(words)
        if not words:
            return
        if words[0] == LOOP_CLOSING_KEYWORD:
            self._close_loop()
            return
        if words[0] in ITERATION_LOOP_KEYWORDS:
            self.open_loops.append(ShellLoop(polls=_iterates_a_counter(words)))
            return
        self._read_condition_or_command(words)

    def _read_condition_or_command(self, words):
        if words[0] in CONDITION_LOOP_KEYWORDS:
            self.open_loops.append(ShellLoop(polls=True))
            words = words[1:]
        self._read_command_words(words_after_command_wrappers(words))

    def _close_loop(self):
        if len(self.open_loops) > self.inherited_loop_count:
            self.open_loops.pop()

    def _read_command_words(self, words):
        if not words:
            return
        command_name = words[0].rsplit("/", 1)[-1]
        reader = COMMAND_READERS_BY_NAME.get(command_name)
        if reader is None and PYTHON_INTERPRETER_PATTERN.fullmatch(command_name):
            reader = _read_python_command
        if reader is not None:
            reader(self, words)

    def record_delay(self, seconds, loop=None):
        self.delays.append(ShellDelay(seconds, loop or self.innermost_loop()))


def _words_after_leading_keywords(words):
    while words and words[0] in KEYWORDS_BEFORE_A_LOOP:
        words = words[1:]
    return words


def _iterates_a_counter(words):
    if words[1:2] and words[1].startswith("(("):
        return True
    loop_items = words[3:] if words[2:3] == ["in"] else []
    return any(COUNTER_ITEM_PATTERN.search(item) for item in loop_items)


def _read_sleep_command(scan, words):
    if sleep_is_a_delay(words[1:]):
        scan.record_delay(sleep_seconds(words[1:]))


def _read_loop_exit_command(scan, _words):
    innermost_loop = scan.innermost_loop()
    if innermost_loop is not None:
        innermost_loop.polls = True


def _read_watch_command(scan, words):
    interval_seconds = WATCH_DEFAULT_INTERVAL_SECONDS
    if len(words) > 2 and words[1] in ("-n", "--interval"):
        interval_seconds = duration_word_seconds(words[2])
    scan.record_delay(interval_seconds, ShellLoop(polls=True))


def _read_shell_command(scan, words):
    script_text = inline_program_after_option(words)
    if script_text is not None:
        scan.delays.extend(delays_in_shell_text(script_text, scan.innermost_loop()))


def _read_python_command(scan, words):
    program_text = inline_program_after_option(words)
    if program_text is None:
        return
    sleep_durations = python_program_sleep_durations(program_text)
    if sleep_durations is not None:
        scan.record_delay(python_program_sleep_seconds(sleep_durations))


COMMAND_READERS_BY_NAME = {
    "sleep": _read_sleep_command,
    "watch": _read_watch_command,
    **dict.fromkeys(LOOP_EXIT_COMMANDS, _read_loop_exit_command),
    **dict.fromkeys(SHELL_INTERPRETERS, _read_shell_command),
}


def delays_in_shell_text(shell_text, enclosing_loop=None):
    scan = _DelayScan(enclosing_loop)
    for words in simple_commands_in(shell_text):
        scan.read_simple_command(words)
    return scan.delays
