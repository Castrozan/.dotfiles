from __future__ import annotations

from background_wait_shape_classifier import (
    command_is_a_background_wait,
    find_unlisted_background_wait_rules,
    known_good_background_wait_shape,
)
from shell_read_only_inspection_command import command_text_the_shell_executes

NOT_A_WAIT = "not-a-wait"


def wait_guard_denial_rule_names(tool_name, command):
    return find_unlisted_background_wait_rules(
        command_text_the_shell_executes(command), tool_name
    )


def wait_shape_name(tool_name, command):
    executed_command_text = command_text_the_shell_executes(command)
    if not command_is_a_background_wait(executed_command_text):
        return NOT_A_WAIT
    return known_good_background_wait_shape(executed_command_text, tool_name)
