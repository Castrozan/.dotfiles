import monitor_streaming_pattern_validator_handler as sut


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
