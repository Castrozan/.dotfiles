from __future__ import annotations

import re

from shell_command_segment_scanning import UNQUOTED_STATE, quote_state_by_offset

MONITOR_TOOL_NAME = "Monitor"

SHELL_LOOP_KEYWORD_PATTERN = re.compile(
    r"(?:^|[;&|({\n]|\b(?:do|then|else)\s)\s*(until|while|for)(?=\s)"
)
SHELL_LOOP_BODY_OPENER_PATTERN = re.compile(r"[;\n]\s*do(?=\s|$)")
SHELL_LOOP_CLOSER_PATTERN = re.compile(r"(?<![\w-])done(?![\w-])")
PACING_SLEEP_PATTERN = re.compile(r"(?<![A-Za-z0-9_/.-])sleep\s+[\"']?[0-9.$]")

PEER_STATE_READ_PATTERN = re.compile(
    r"\borchestrator\s+report\s+(?:show|list)\b"
    r"|\bherdr\s+(?:--\S+\s+\S+\s+)*(?:agent|pane)\s+read\b"
    r"|\ba2a\s+(?:status|inbox)\b"
)
PEER_EVENT_STREAM_PATTERN = re.compile(r"\borchestrator\s+watch\b")
PEER_LIVENESS_PROBE_PATTERN = re.compile(
    r"\bherdr\s+(?:--\S+\s+\S+\s+)*pane\s+(?:get|list|process-info)\b"
    r"|\bherdr\s+(?:--\S+\s+\S+\s+)*agent\s+(?:get|list)\b"
    r"|\ba2a\s+list\b"
    r"|\bkill\s+-0\b"
    r"|\bpgrep\b"
    r"|\bps\s+-p\b"
)


def shell_loop_span(command_string):
    quote_states = quote_state_by_offset(command_string)
    unquoted_loop_keyword_offsets = [
        loop_keyword.start(1)
        for loop_keyword in SHELL_LOOP_KEYWORD_PATTERN.finditer(command_string)
        if quote_states[loop_keyword.start(1)] == UNQUOTED_STATE
    ]
    if not unquoted_loop_keyword_offsets:
        return None
    loop_start = unquoted_loop_keyword_offsets[0]
    if not SHELL_LOOP_BODY_OPENER_PATTERN.search(command_string, loop_start):
        return None
    loop_closers = list(SHELL_LOOP_CLOSER_PATTERN.finditer(command_string, loop_start))
    loop_end = loop_closers[-1].end() if loop_closers else len(command_string)
    return loop_start, loop_end


def pattern_matches_inside_a_shell_loop(pattern, command_string):
    loop_span = shell_loop_span(command_string)
    if loop_span is None:
        return False
    loop_start, loop_end = loop_span
    return bool(pattern.search(command_string, loop_start, loop_end))


def command_polls_peer_state_in_a_loop(command_string):
    return pattern_matches_inside_a_shell_loop(PEER_STATE_READ_PATTERN, command_string)


def command_streams_peer_events(command_string):
    return bool(PEER_EVENT_STREAM_PATTERN.search(command_string))


def command_polls_in_a_sleep_paced_loop(command_string):
    return pattern_matches_inside_a_shell_loop(PACING_SLEEP_PATTERN, command_string)


def command_is_a_background_wait(command_string):
    return (
        command_streams_peer_events(command_string)
        or command_polls_peer_state_in_a_loop(command_string)
        or command_polls_in_a_sleep_paced_loop(command_string)
    )


def _is_a_peer_event_stream_under_monitor(command_string, tool_name):
    return tool_name == MONITOR_TOOL_NAME and command_streams_peer_events(
        command_string
    )


def _is_a_peer_poll_with_a_liveness_exit(command_string, tool_name):
    return (
        command_polls_peer_state_in_a_loop(command_string)
        and not command_streams_peer_events(command_string)
        and pattern_matches_inside_a_shell_loop(
            PEER_LIVENESS_PROBE_PATTERN, command_string
        )
    )


def _is_a_condition_poll(command_string, tool_name):
    return (
        command_polls_in_a_sleep_paced_loop(command_string)
        and not command_polls_peer_state_in_a_loop(command_string)
        and not command_streams_peer_events(command_string)
    )


KNOWN_GOOD_WAIT_SHAPE_MATCHERS_BY_NAME = {
    "peer-event-stream-under-monitor": _is_a_peer_event_stream_under_monitor,
    "peer-poll-with-liveness-exit": _is_a_peer_poll_with_a_liveness_exit,
    "condition-poll": _is_a_condition_poll,
}


def known_good_background_wait_shape(command_string, tool_name):
    for shape_name, matches in KNOWN_GOOD_WAIT_SHAPE_MATCHERS_BY_NAME.items():
        if matches(command_string, tool_name):
            return shape_name
    return None


def find_unlisted_background_wait_rules(command_string, tool_name):
    if not command_is_a_background_wait(command_string):
        return []
    if known_good_background_wait_shape(command_string, tool_name):
        return []
    if command_streams_peer_events(command_string):
        return ["peer-event-stream-outside-monitor"]
    return ["peer-wait-without-liveness-exit"]


BACKGROUND_WAIT_SHAPES_REFERENCE_FILE_PATH = (
    "~/.claude/hooks/background-bash-anti-patterns.md"
)

UNLISTED_BACKGROUND_WAIT_EXPLANATIONS_BY_RULE_NAME = {
    "peer-wait-without-liveness-exit": (
        "It polls a peer agent's state in a loop and never checks that the peer "
        "is still there, so once the peer's pane closes the state it reads is "
        "frozen and the loop stays silent until its cap, or forever. Make the "
        "loop also exit, printing why, when the peer is gone: add "
        "'|| ! herdr pane get <pane> >/dev/null 2>&1' to the exit condition and "
        "echo PEER-GONE after the loop when that probe fails."
    ),
    "peer-event-stream-outside-monitor": (
        "It runs 'orchestrator watch' in backgrounded Bash, which notifies only "
        "when the command exits, and that stream never exits. Run the same "
        "command with the Monitor tool, which delivers each line as an event."
    ),
}


def build_unlisted_background_wait_deny_reason(
    triggered_rule_names, execution_context_label
):
    rules_list_text = ", ".join(triggered_rule_names)
    explanations_text = " ".join(
        UNLISTED_BACKGROUND_WAIT_EXPLANATIONS_BY_RULE_NAME[rule_name]
        for rule_name in triggered_rule_names
    )
    known_good_shapes_text = ", ".join(KNOWN_GOOD_WAIT_SHAPE_MATCHERS_BY_NAME)
    return (
        f"{execution_context_label} is a background wait outside the known-good "
        f"shapes: {rules_list_text}. {explanations_text} Allowed waits: a native "
        f"blocking wait such as 'herdr agent wait <pane> --until done --timeout "
        f"<ms>', or a loop matching {known_good_shapes_text}. Read "
        f"{BACKGROUND_WAIT_SHAPES_REFERENCE_FILE_PATH} for each shape, then retry."
    )
