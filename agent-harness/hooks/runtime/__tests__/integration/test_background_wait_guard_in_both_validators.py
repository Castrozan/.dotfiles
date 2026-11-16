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

PEER_POLL_WITHOUT_LIVENESS_EXIT = (
    'until [ -n "$(orchestrator report show Reviewer-w4E-p6)" ]; do sleep 45; done'
)
PEER_POLL_WITH_LIVENESS_EXIT = (
    'until [ -n "$(orchestrator report show Reviewer-w4E-p6)" ] '
    "|| ! herdr pane get w4E:p6 >/dev/null 2>&1; do sleep 45; done"
)
PEER_EVENT_STREAM = "orchestrator watch --workspace w4E --timeout-minutes 10"


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


class TestBackgroundedBash:
    def test_a_peer_poll_without_a_liveness_exit_is_denied_with_the_fix(self):
        result = background_bash_validator.handle(
            bash_tool_call(PEER_POLL_WITHOUT_LIVENESS_EXIT, run_in_background=True)
        )

        assert result is not None
        assert result.decision == "deny"
        assert "The backgrounded Bash command" in result.reason
        assert "peer-wait-without-liveness-exit" in result.reason
        assert "herdr pane get <pane>" in result.reason
        assert "PEER-GONE" in result.reason
        assert "herdr agent wait" in result.reason
        assert "peer-poll-with-liveness-exit" in result.reason
        assert "background-bash-anti-patterns.md" in result.reason

    def test_a_peer_event_stream_is_denied_and_sent_to_monitor(self):
        result = background_bash_validator.handle(
            bash_tool_call(PEER_EVENT_STREAM, run_in_background=True)
        )

        assert result is not None
        assert "peer-event-stream-outside-monitor" in result.reason
        assert "Monitor tool" in result.reason

    def test_the_same_poll_with_a_liveness_exit_is_allowed(self):
        assert (
            background_bash_validator.handle(
                bash_tool_call(PEER_POLL_WITH_LIVENESS_EXIT, run_in_background=True)
            )
            is None
        )

    def test_a_foreground_peer_poll_is_outside_the_background_wait_guard(self):
        assert (
            background_bash_validator.handle(
                bash_tool_call(PEER_POLL_WITHOUT_LIVENESS_EXIT, run_in_background=False)
            )
            is None
        )


class TestMonitor:
    def test_a_peer_poll_without_a_liveness_exit_is_denied(self):
        result = monitor_validator.handle(
            monitor_tool_call(PEER_POLL_WITHOUT_LIVENESS_EXIT)
        )

        assert result is not None
        assert result.decision == "deny"
        assert "Monitor is a background wait outside the known-good shapes" in (
            result.reason
        )
        assert "peer-wait-without-liveness-exit" in result.reason

    def test_a_peer_poll_with_a_liveness_exit_is_allowed(self):
        assert (
            monitor_validator.handle(monitor_tool_call(PEER_POLL_WITH_LIVENESS_EXIT))
            is None
        )

    def test_a_peer_event_stream_is_allowed(self):
        assert monitor_validator.handle(monitor_tool_call(PEER_EVENT_STREAM)) is None
