from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from hook_dispatch import HandlerResult  # noqa: E402

BASH_TOOL_NAME = "Bash"
MONITOR_TOOL_NAME = "Monitor"
DELAY_COMMAND_WORDS = ("sleep", "watch")
EXECUTION_CONTEXT_LABEL_BY_CONTEXT = {
    (BASH_TOOL_NAME, False): "This Bash command",
    (BASH_TOOL_NAME, True): "The backgrounded Bash command",
    (MONITOR_TOOL_NAME, False): "Monitor",
}


def handle(hook_input):
    tool_name = hook_input.get("tool_name")
    if tool_name not in (BASH_TOOL_NAME, MONITOR_TOOL_NAME):
        return None
    tool_input = hook_input.get("tool_input", {})
    command_string = _command_with_a_delay_word(tool_input)
    if not command_string:
        return None
    runs_in_background = tool_input.get("run_in_background") is True
    return _delay_wait_result(command_string, tool_name, runs_in_background)


def _command_with_a_delay_word(tool_input):
    command_string = tool_input.get("command", "")
    if not isinstance(command_string, str):
        return ""
    if any(delay_word in command_string for delay_word in DELAY_COMMAND_WORDS):
        return command_string
    return ""


def _delay_wait_result(command_string, tool_name, runs_in_background):
    from background_wait_shape_classifier import (
        build_delay_wait_deny_reason,
        find_denied_delay_wait,
    )

    delay_wait = find_denied_delay_wait(command_string, tool_name, runs_in_background)
    if delay_wait is None:
        return None
    execution_context_label = EXECUTION_CONTEXT_LABEL_BY_CONTEXT.get(
        (tool_name, runs_in_background), MONITOR_TOOL_NAME
    )
    return HandlerResult(
        decision="deny",
        reason=build_delay_wait_deny_reason(delay_wait, execution_context_label),
    )
