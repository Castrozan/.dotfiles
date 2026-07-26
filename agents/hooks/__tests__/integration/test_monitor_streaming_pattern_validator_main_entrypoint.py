import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

monitor_streaming_pattern_validator_handler = import_hyphenated_hook_module(
    "monitor_streaming_pattern_validator_handler"
)


class TestHandle:
    def build_monitor_pre_tool_use_input(self, command, tool_name="Monitor"):
        return {
            "session_id": "test-session",
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {
                "description": "test",
                "timeout_ms": 30000,
                "persistent": False,
                "command": command,
            },
        }

    def test_denies_command_with_python_buffering(self):
        result = monitor_streaming_pattern_validator_handler.handle(
            self.build_monitor_pre_tool_use_input("python3 worker.py")
        )
        assert result is not None
        assert result.decision == "deny"
        assert "python-without-u" in result.reason
        assert "monitor-streaming-patterns.md" in result.reason

    def test_denies_multiple_rules_in_one_message(self):
        result = monitor_streaming_pattern_validator_handler.handle(
            self.build_monitor_pre_tool_use_input("python3 w.py | grep ERROR")
        )
        assert result is not None
        assert "python-without-u" in result.reason
        assert "grep-without-line-buffered" in result.reason

    def test_allows_clean_command(self):
        result = monitor_streaming_pattern_validator_handler.handle(
            self.build_monitor_pre_tool_use_input(
                "tail -f /var/log/app.log | grep --line-buffered ERROR"
            )
        )
        assert result is None

    def test_skips_non_monitor_tools(self):
        result = monitor_streaming_pattern_validator_handler.handle(
            self.build_monitor_pre_tool_use_input("python3 worker.py", tool_name="Bash")
        )
        assert result is None

    def test_skips_empty_command(self):
        result = monitor_streaming_pattern_validator_handler.handle(
            {"hook_event_name": "PreToolUse", "tool_name": "Monitor", "tool_input": {}}
        )
        assert result is None
