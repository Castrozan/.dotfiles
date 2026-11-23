import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

background_bash_validator = import_hyphenated_hook_module(
    "background_bash_anti_pattern_validator_handler"
)
monitor_validator = import_hyphenated_hook_module(
    "monitor_streaming_pattern_validator_handler"
)
delay_wait_guard = import_hyphenated_hook_module("delay_wait_guard_handler")

PEER_POLL_WITH_LIVENESS_EXIT = (
    'until [ -n "$(orchestrator heartbeat show Reviewer-w4E-p6)" ] '
    "|| ! herdr pane get w4E:p6 >/dev/null 2>&1; do sleep 45; done"
)
PEER_EVENT_STREAM = "orchestrator watch --workspace w4E --timeout-minutes 10"
UNCAPPED_MERGE_REQUEST_POLL = (
    "until [ \"$(glab api 'projects/group%2Fplugin/merge_requests/118' "
    '| jq -r .state)" = merged ]; do sleep 30; done'
)


def bash_tool_call(command, run_in_background):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command, "run_in_background": run_in_background},
    }


def monitor_tool_call(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Monitor",
        "tool_input": {"command": command, "description": "watch a peer"},
    }


class TestPeerPollsBelongToTheDelayWaitGuard:
    def test_a_peer_poll_is_denied_in_backgrounded_bash_with_its_event(self):
        result = delay_wait_guard.handle(
            bash_tool_call(PEER_POLL_WITH_LIVENESS_EXIT, run_in_background=True)
        )

        assert result.decision == "deny"
        assert "The backgrounded Bash command" in result.reason
        assert "(sleep-paced-loop on peer-agent)" in result.reason
        assert "herdr agent wait" in result.reason
        assert "orchestrator status" in result.reason
        assert "background-bash-anti-patterns.md" in result.reason

    def test_a_peer_poll_is_denied_under_monitor(self):
        result = delay_wait_guard.handle(
            monitor_tool_call(PEER_POLL_WITH_LIVENESS_EXIT)
        )

        assert result.decision == "deny"
        assert result.reason.startswith("Monitor waits by sleeping in a loop")

    def test_neither_validator_repeats_the_delay_denial(self):
        assert (
            background_bash_validator.handle(
                bash_tool_call(PEER_POLL_WITH_LIVENESS_EXIT, run_in_background=True)
            )
            is None
        )
        assert (
            monitor_validator.handle(monitor_tool_call(PEER_POLL_WITH_LIVENESS_EXIT))
            is None
        )


class TestBackgroundedBash:
    def test_a_peer_event_stream_is_denied_and_sent_to_monitor(self):
        result = background_bash_validator.handle(
            bash_tool_call(PEER_EVENT_STREAM, run_in_background=True)
        )

        assert "peer-event-stream-outside-monitor" in result.reason
        assert "Monitor tool" in result.reason

    def test_an_uncapped_remote_poll_is_denied_for_its_missing_cap(self):
        result = background_bash_validator.handle(
            bash_tool_call(UNCAPPED_MERGE_REQUEST_POLL, run_in_background=True)
        )

        assert "forge-poll-without-cap" in result.reason
        assert "remote-state-safety-net" in result.reason


class TestMonitor:
    def test_a_peer_event_stream_is_allowed(self):
        assert monitor_validator.handle(monitor_tool_call(PEER_EVENT_STREAM)) is None
        assert delay_wait_guard.handle(monitor_tool_call(PEER_EVENT_STREAM)) is None
