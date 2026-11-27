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
WAITER_COMMAND_MARKERS = ("herdr", "wait-for-event", "hypruse", "docker", "ci-watcher")
BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH = (
    "~/.claude/hooks/background-bash-anti-patterns.md"
)


def handle(hook_input):
    command_string = _foreground_bash_command(hook_input)
    if not any(marker in command_string for marker in WAITER_COMMAND_MARKERS):
        return None
    return _foreground_event_wait_result(command_string)


def _foreground_bash_command(hook_input):
    tool_input = hook_input.get("tool_input", {})
    if hook_input.get("tool_name") != BASH_TOOL_NAME or (
        tool_input.get("run_in_background") is True
    ):
        return ""
    command_string = tool_input.get("command", "")
    return command_string if isinstance(command_string, str) else ""


def _foreground_event_wait_result(command_string):
    from foreground_event_wait_detectors import (
        build_foreground_event_wait_deny_reason,
        foreground_event_wait_in,
    )

    foreground_event_wait = foreground_event_wait_in(command_string)
    if foreground_event_wait is None:
        return None
    return HandlerResult(
        decision="deny",
        reason=build_foreground_event_wait_deny_reason(
            foreground_event_wait, BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH
        ),
    )
