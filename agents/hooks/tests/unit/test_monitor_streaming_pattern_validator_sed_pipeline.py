import pytest

import monitor_streaming_pattern_validator as sut


class TestCommandPipesIntoSedWithoutUnbufferedFlag:
    @pytest.mark.parametrize(
        "command",
        [
            "tail -f log | sed 's/foo/bar/'",
            "cat file | sed -e 's/x/y/'",
        ],
    )
    def test_flags_sed_without_unbuffered(self, command):
        assert sut.command_pipes_into_sed_without_unbuffered_flag(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "tail -f log | sed -u 's/foo/bar/'",
            "tail -f log | sed --unbuffered 's/foo/bar/'",
        ],
    )
    def test_passes_sed_with_unbuffered(self, command):
        assert sut.command_pipes_into_sed_without_unbuffered_flag(command) is False
