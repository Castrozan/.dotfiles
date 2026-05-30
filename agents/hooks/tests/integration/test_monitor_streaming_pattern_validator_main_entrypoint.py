import json
from io import StringIO
from unittest.mock import patch

import pytest

import monitor_streaming_pattern_validator as sut


class TestMain:
    def build_monitor_pre_tool_use_input(self, command, tool_name="Monitor"):
        return json.dumps(
            {
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
        )

    def run_main_and_capture_stdout(self, hook_input_json):
        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO(hook_input_json)),
            patch("sys.stdout", captured_stdout),
            pytest.raises(SystemExit) as exit_info,
        ):
            sut.main()
        return exit_info.value.code, captured_stdout.getvalue()

    def test_denies_command_with_python_buffering(self):
        hook_input = self.build_monitor_pre_tool_use_input("python3 worker.py")
        exit_code, stdout_text = self.run_main_and_capture_stdout(hook_input)
        assert exit_code == 0
        payload = json.loads(stdout_text)
        decision = payload["hookSpecificOutput"]["permissionDecision"]
        assert decision == "deny"
        reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
        assert "python-without-u" in reason
        assert "monitor-streaming-patterns.md" in reason

    def test_denies_multiple_rules_in_one_message(self):
        hook_input = self.build_monitor_pre_tool_use_input("python3 w.py | grep ERROR")
        exit_code, stdout_text = self.run_main_and_capture_stdout(hook_input)
        payload = json.loads(stdout_text)
        reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
        assert "python-without-u" in reason
        assert "grep-without-line-buffered" in reason

    def test_allows_clean_command(self):
        hook_input = self.build_monitor_pre_tool_use_input(
            "tail -f /var/log/app.log | grep --line-buffered ERROR"
        )
        exit_code, stdout_text = self.run_main_and_capture_stdout(hook_input)
        assert exit_code == 0
        assert stdout_text == ""

    def test_skips_non_monitor_tools(self):
        hook_input = self.build_monitor_pre_tool_use_input(
            "python3 worker.py", tool_name="Bash"
        )
        exit_code, stdout_text = self.run_main_and_capture_stdout(hook_input)
        assert exit_code == 0
        assert stdout_text == ""

    def test_skips_empty_command(self):
        hook_input = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Monitor",
                "tool_input": {},
            }
        )
        exit_code, stdout_text = self.run_main_and_capture_stdout(hook_input)
        assert exit_code == 0
        assert stdout_text == ""

    def test_exits_silently_on_invalid_json(self):
        exit_code, _ = self.run_main_and_capture_stdout("not json")
        assert exit_code == 0
