from __future__ import annotations

import re
from collections import namedtuple

from shell_data_heredoc_bodies import shell_text_outside_data_heredoc_bodies
from shell_delay_commands import delays_in_shell_text
from shell_read_only_inspection_command import command_text_the_shell_executes
from wait_target_event_replacements import (
    EVENT_REPLACEMENT_BY_WAIT_TARGET,
    waited_target,
)

MONITOR_TOOL_NAME = "Monitor"
SLEEP_PACED_LOOP_RULE = "sleep-paced-loop"
FIXED_DELAY_RULE = "fixed-delay"
PEER_EVENT_STREAM_OUTSIDE_MONITOR_RULE = "peer-event-stream-outside-monitor"
PEER_EVENT_STREAM_UNDER_MONITOR_SHAPE = "peer-event-stream-under-monitor"

PEER_EVENT_STREAM_PATTERN = re.compile(r"\borchestrator\s+watch\b")


DelayWait = namedtuple("DelayWait", "rule_name target_name")


def delay_wait_in(command_string):
    shell_text = shell_text_outside_data_heredoc_bodies(command_string)
    waiting_delays = [
        delay for delay in delays_in_shell_text(shell_text) if not delay.paces_input
    ]
    if not waiting_delays:
        return None
    sleeps_in_a_loop = any(delay.loop is not None for delay in waiting_delays)
    rule_name = SLEEP_PACED_LOOP_RULE if sleeps_in_a_loop else FIXED_DELAY_RULE
    return DelayWait(rule_name, waited_target(shell_text))


def command_streams_peer_events(command_string):
    return bool(PEER_EVENT_STREAM_PATTERN.search(command_string))


def command_is_a_background_wait(command_string):
    return command_streams_peer_events(command_string) or (
        delay_wait_in(command_string) is not None
    )


def known_good_background_wait_shape(command_string, tool_name):
    executed_command_text = command_text_the_shell_executes(command_string)
    if tool_name == MONITOR_TOOL_NAME and command_streams_peer_events(
        executed_command_text
    ):
        return PEER_EVENT_STREAM_UNDER_MONITOR_SHAPE
    return None


def find_unlisted_background_wait_rules(command_string, tool_name):
    if tool_name != MONITOR_TOOL_NAME and command_streams_peer_events(command_string):
        return [PEER_EVENT_STREAM_OUTSIDE_MONITOR_RULE]
    return []


BACKGROUND_WAIT_SHAPES_REFERENCE_FILE_PATH = (
    "~/.claude/hooks/background-bash-anti-patterns.md"
)

UNLISTED_BACKGROUND_WAIT_EXPLANATIONS_BY_RULE_NAME = {
    PEER_EVENT_STREAM_OUTSIDE_MONITOR_RULE: (
        "It runs 'orchestrator watch' in backgrounded Bash, which notifies only "
        "when the command exits, and that stream never exits. Run the same "
        "command with the Monitor tool, which delivers each line as an event."
    ),
}

DELAY_PHRASE_BY_RULE_NAME = {
    SLEEP_PACED_LOOP_RULE: "sleeping in a loop",
    FIXED_DELAY_RULE: "sleeping a fixed time",
}


def build_unlisted_background_wait_deny_reason(
    triggered_rule_names, execution_context_label
):
    rules_list_text = ", ".join(triggered_rule_names)
    explanations_text = " ".join(
        UNLISTED_BACKGROUND_WAIT_EXPLANATIONS_BY_RULE_NAME[rule_name]
        for rule_name in triggered_rule_names
    )
    return (
        f"{execution_context_label} is a background wait outside the known-good "
        f"shapes: {rules_list_text}. {explanations_text} Allowed waits: a native "
        f"blocking wait such as 'herdr agent wait <pane> --until done --timeout "
        f"<ms>', or a wait matching {PEER_EVENT_STREAM_UNDER_MONITOR_SHAPE}. Read "
        f"{BACKGROUND_WAIT_SHAPES_REFERENCE_FILE_PATH} for each shape, then retry."
    )


def build_delay_wait_deny_reason(delay_wait, execution_context_label):
    delay_phrase = DELAY_PHRASE_BY_RULE_NAME[delay_wait.rule_name]
    return (
        f"{execution_context_label} waits by {delay_phrase} ({delay_wait.rule_name} "
        f"on {delay_wait.target_name}) instead of on an event. See "
        f"{BACKGROUND_WAIT_SHAPES_REFERENCE_FILE_PATH}.\n"
        "Wait on the event instead: "
        f"{EVENT_REPLACEMENT_BY_WAIT_TARGET[delay_wait.target_name]}"
    )
