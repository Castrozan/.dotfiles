import pytest

import monitor_streaming_pattern_validator as sut


class TestCommandPipesIntoAwk:
    @pytest.mark.parametrize(
        "command",
        [
            "tail -f log | awk '{print}'",
            "cat file | gawk '/ERROR/'",
            "cat file | mawk '{print $1}'",
        ],
    )
    def test_flags_any_awk_in_pipeline(self, command):
        assert sut.command_pipes_into_awk(command) is True

    def test_ignores_awk_not_in_pipeline(self):
        assert sut.command_pipes_into_awk("awk '{print}' file.txt") is False
