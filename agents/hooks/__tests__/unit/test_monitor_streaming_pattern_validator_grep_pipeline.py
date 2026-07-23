import pytest

import monitor_streaming_pattern_validator as sut


class TestCommandPipesIntoGrepWithoutLineBufferedFlag:
    @pytest.mark.parametrize(
        "command",
        [
            "tail -f log | grep ERROR",
            "journalctl -f | egrep 'WARN|ERROR'",
            "cat file | grep -i pattern",
        ],
    )
    def test_flags_grep_without_line_buffered(self, command):
        assert sut.command_pipes_into_grep_without_line_buffered_flag(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "tail -f log | grep --line-buffered ERROR",
            "journalctl -f | grep --line-buffered -E 'WARN|ERROR'",
            "echo hi | grep --line-buffered hi",
        ],
    )
    def test_passes_grep_with_line_buffered(self, command):
        assert sut.command_pipes_into_grep_without_line_buffered_flag(command) is False

    def test_ignores_grep_not_in_pipeline(self):
        assert (
            sut.command_pipes_into_grep_without_line_buffered_flag(
                "grep ERROR file.txt"
            )
            is False
        )
