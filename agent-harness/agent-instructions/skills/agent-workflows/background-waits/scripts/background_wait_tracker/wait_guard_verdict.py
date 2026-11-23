from __future__ import annotations

from background_wait_shape_classifier import (
    command_is_a_background_wait,
    find_denied_delay_wait,
    find_unlisted_background_wait_rules,
    known_good_background_wait_shape,
)
from shell_read_only_inspection_command import command_text_the_shell_executes

NOT_A_WAIT = "not-a-wait"


def wait_guard_denial_rule_names(tool_name, command):
    denied_delay_wait = find_denied_delay_wait(command, tool_name, True)
    delay_rule_names = [denied_delay_wait.rule_name] if denied_delay_wait else []
    return delay_rule_names + find_unlisted_background_wait_rules(
        command_text_the_shell_executes(command), tool_name
    )


def wait_shape_name(tool_name, command):
    if not command_is_a_background_wait(command):
        return NOT_A_WAIT
    return known_good_background_wait_shape(command, tool_name)
