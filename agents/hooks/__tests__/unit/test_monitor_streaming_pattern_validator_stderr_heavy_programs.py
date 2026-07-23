import pytest

import monitor_streaming_pattern_validator as sut


class TestCommandRunsKnownStderrHeavyProgramWithoutRedirect:
    @pytest.mark.parametrize(
        "command",
        [
            "git fetch --verbose origin",
            "git push origin main",
            "curl -v https://example.com",
            "npm install",
            "cargo build --release",
            "make all",
        ],
    )
    def test_flags_known_stderr_heavy_programs(self, command):
        assert (
            sut.command_runs_known_stderr_heavy_program_without_redirect(command)
            is True
        )

    @pytest.mark.parametrize(
        "command",
        [
            "git fetch --verbose origin 2>&1",
            "curl -v https://example.com 2>&1",
            "make all 2>&1",
        ],
    )
    def test_passes_when_stderr_redirected(self, command):
        assert (
            sut.command_runs_known_stderr_heavy_program_without_redirect(command)
            is False
        )

    @pytest.mark.parametrize(
        "command",
        [
            "git log --oneline",
            "echo hi",
            "tail -f file",
        ],
    )
    def test_ignores_unknown_or_quiet_commands(self, command):
        assert (
            sut.command_runs_known_stderr_heavy_program_without_redirect(command)
            is False
        )
