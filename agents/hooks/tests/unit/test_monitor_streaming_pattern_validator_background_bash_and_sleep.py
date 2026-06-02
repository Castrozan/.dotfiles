import monitor_streaming_pattern_validator as sut
import pytest


class TestStreamedOrBackgroundedContextGate:
    def test_monitor_is_in_scope(self):
        assert sut.command_runs_in_a_streamed_or_backgrounded_context("Monitor", {})

    def test_backgrounded_bash_is_in_scope(self):
        assert sut.command_runs_in_a_streamed_or_backgrounded_context(
            "Bash", {"command": "x", "run_in_background": True}
        )

    def test_foreground_bash_is_out_of_scope(self):
        assert not sut.command_runs_in_a_streamed_or_backgrounded_context(
            "Bash", {"command": "x"}
        )

    def test_unrelated_tool_is_out_of_scope(self):
        assert not sut.command_runs_in_a_streamed_or_backgrounded_context("Read", {})


class TestBlindSleepWaitRule:
    @pytest.mark.parametrize(
        "command",
        [
            "sleep 30 && curl localhost:8767",
            "for i in $(seq 1 60); do sleep 5; check; done",
            "sleep 0.5",
        ],
    )
    def test_blind_sleep_is_flagged(self, command):
        assert "blind-sleep-wait" in sut.find_busy_wait_anti_patterns_in_command(
            command
        )

    @pytest.mark.parametrize(
        "command",
        [
            "curl --max-time 5 localhost:8767",
            "git sleeper_branch checkout",
            "cat /tmp/sleep.log",
        ],
    )
    def test_non_blind_wait_commands_are_not_flagged(self, command):
        assert sut.find_busy_wait_anti_patterns_in_command(command) == []
