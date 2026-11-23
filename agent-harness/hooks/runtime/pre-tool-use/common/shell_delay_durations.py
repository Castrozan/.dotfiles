from __future__ import annotations

import re

SLEEP_DURATION_PATTERN = re.compile(r"(\d*\.?\d+)([smhd]?)")
SECONDS_PER_DURATION_SUFFIX = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
KEEP_ALIVE_DURATIONS = frozenset({"infinity", "inf"})


def duration_word_seconds(duration_word):
    duration_match = SLEEP_DURATION_PATTERN.fullmatch(duration_word)
    if duration_match is None:
        return None
    amount, suffix = duration_match.groups()
    return float(amount) * SECONDS_PER_DURATION_SUFFIX[suffix]


def sleep_seconds(duration_words):
    durations = [duration_word_seconds(word) for word in duration_words]
    if not durations or None in durations:
        return None
    return sum(durations)


def sleep_is_a_delay(duration_words):
    if not duration_words or duration_words[0].startswith("-"):
        return False
    return not KEEP_ALIVE_DURATIONS.intersection(duration_words)


def inline_program_after_option(words):
    for option_index, word in enumerate(words[1:-1], start=1):
        if word.startswith("-") and not word.startswith("--") and "c" in word:
            return words[option_index + 1]
    return None


def _sleep_call_duration(statement):
    import ast

    call = getattr(statement, "value", None)
    if not isinstance(call, ast.Call) or len(call.args) != 1:
        return None
    called_name = getattr(call.func, "attr", None) or getattr(call.func, "id", None)
    return call.args[0] if called_name == "sleep" else None


def _statements_after_imports(program_text):
    import ast

    try:
        statements = ast.parse(program_text).body
    except SyntaxError:
        return []
    return [
        statement
        for statement in statements
        if not isinstance(statement, (ast.Import, ast.ImportFrom))
    ]


def python_program_sleep_durations(program_text):
    durations = [
        _sleep_call_duration(statement)
        for statement in _statements_after_imports(program_text)
    ]
    if not durations or None in durations:
        return None
    return durations


def python_program_sleep_seconds(sleep_durations):
    import ast

    if not all(
        isinstance(duration, ast.Constant) and isinstance(duration.value, (int, float))
        for duration in sleep_durations
    ):
        return None
    return float(sum(duration.value for duration in sleep_durations))
