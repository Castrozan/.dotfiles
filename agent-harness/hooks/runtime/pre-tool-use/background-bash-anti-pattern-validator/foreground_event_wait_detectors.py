from __future__ import annotations

from collections import namedtuple

from shell_command_wrappers import command_inside_wrappers
from shell_data_heredoc_bodies import shell_text_outside_data_heredoc_bodies
from shell_delay_durations import duration_word_seconds
from shell_simple_commands import simple_commands_in

FOREGROUND_WAIT_CEILING_SECONDS = 30.0
SECONDS_PER_MILLISECOND = 0.001
HYPRUSE_DEFAULT_TIMEOUT_WORD = "10"
HELP_WORDS = frozenset({"--help", "-h"})
HERDR_WAIT_SUBCOMMANDS = (["agent", "wait"], ["pane", "wait-output"])
WAIT_FOR_EVENT_SUBCOMMANDS = frozenset({"file", "process"})

WaiterInvocation = namedtuple(
    "WaiterInvocation", "waiter_name own_bound_seconds waits_on_ci"
)
ForegroundEventWait = namedtuple("ForegroundEventWait", "waiter_name waits_on_ci")


def _option_value_word(arguments, option_name):
    for argument_index, argument in enumerate(arguments):
        if argument == option_name:
            return "".join(arguments[argument_index + 1 : argument_index + 2]) or None
        if argument.startswith(option_name + "="):
            return argument[len(option_name) + 1 :]
    return None


def _seconds_in(value_word, seconds_per_unit=1.0):
    if value_word is None:
        return None
    amount = duration_word_seconds(value_word)
    return None if amount is None else amount * seconds_per_unit


def _herdr_wait(arguments):
    if arguments[:2] not in HERDR_WAIT_SUBCOMMANDS:
        return None
    timeout_word = _option_value_word(arguments, "--timeout")
    return WaiterInvocation(
        "herdr " + " ".join(arguments[:2]),
        _seconds_in(timeout_word, SECONDS_PER_MILLISECOND),
        False,
    )


def _wait_for_event(arguments):
    if arguments[:1] == [] or arguments[0] not in WAIT_FOR_EVENT_SUBCOMMANDS:
        return None
    timeout_word = _option_value_word(arguments, "--timeout-seconds")
    return WaiterInvocation("wait-for-event", _seconds_in(timeout_word), False)


def _hypruse_wait(arguments):
    if arguments[:1] != ["wait_for"]:
        return None
    timeout_word = _option_value_word(arguments, "--timeout")
    return WaiterInvocation(
        "hypruse wait_for",
        _seconds_in(timeout_word or HYPRUSE_DEFAULT_TIMEOUT_WORD),
        False,
    )


def _docker_wait(arguments):
    if arguments[:1] != ["wait"]:
        return None
    return WaiterInvocation("docker wait", None, False)


def _ci_watcher(_arguments):
    return WaiterInvocation("ci-watcher", None, True)


WAITER_READERS_BY_COMMAND_NAME = {
    "herdr": _herdr_wait,
    "wait-for-event": _wait_for_event,
    "hypruse": _hypruse_wait,
    "docker": _docker_wait,
    "ci-watcher": _ci_watcher,
}


def _waiter_invocation(command_words):
    if not command_words:
        return None
    reader = WAITER_READERS_BY_COMMAND_NAME.get(command_words[0].rsplit("/", 1)[-1])
    arguments = command_words[1:]
    if reader is None or HELP_WORDS.intersection(arguments):
        return None
    return reader(arguments)


def _tightest_bound_seconds(*bounds_seconds):
    known_bounds = [bound for bound in bounds_seconds if bound is not None]
    return min(known_bounds) if known_bounds else None


def _parks_the_session(waiter, wrapper_bound_seconds):
    if waiter.waits_on_ci:
        return True
    bound_seconds = _tightest_bound_seconds(
        waiter.own_bound_seconds, wrapper_bound_seconds
    )
    return bound_seconds is None or bound_seconds > FOREGROUND_WAIT_CEILING_SECONDS


def foreground_event_wait_in(command_string):
    shell_text = shell_text_outside_data_heredoc_bodies(command_string)
    for words in simple_commands_in(shell_text):
        wrapped_command = command_inside_wrappers(words)
        waiter = _waiter_invocation(wrapped_command.command_words)
        if waiter is None:
            continue
        wrapper_bound_seconds = _seconds_in(wrapped_command.timeout_duration_word)
        if _parks_the_session(waiter, wrapper_bound_seconds):
            return ForegroundEventWait(waiter.waiter_name, waiter.waits_on_ci)
    return None


def build_foreground_event_wait_deny_reason(foreground_event_wait, reference_path):
    limit_sentence = (
        "A CI wait always runs in the background, whatever its bound."
        if foreground_event_wait.waits_on_ci
        else "Only a wait bounded to 30 s or less, by timeout or its own timeout "
        "flag, may stay in the foreground."
    )
    return (
        f"This Bash command parks the session on {foreground_event_wait.waiter_name} "
        "(foreground-event-wait). Rerun it with run_in_background: true and keep "
        f"working; the harness notifies you when it ends. {limit_sentence} "
        f"See {reference_path}."
    )
