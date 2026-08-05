import pytest

import streamed_command_anti_pattern_detectors as sut


class TestCommandInvokesPythonWithBufferedStdout:
    @pytest.mark.parametrize(
        "command",
        [
            "python3 worker.py",
            "python script.py",
            "python3 -c 'print(\"hi\")'",
            "cd /app && python3 main.py",
            "bash -c 'python3 worker.py'",
        ],
    )
    def test_flags_python_without_unbuffered_flag(self, command):
        assert sut.command_invokes_python_with_buffered_stdout(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "python3 -u worker.py",
            "python -u script.py",
            "PYTHONUNBUFFERED=1 python3 worker.py",
            "env PYTHONUNBUFFERED=1 python3 worker.py",
            "python3 -uB script.py",
        ],
    )
    def test_passes_unbuffered_python_invocations(self, command):
        assert sut.command_invokes_python_with_buffered_stdout(command) is False

    @pytest.mark.parametrize(
        "command",
        [
            "tail -f /var/log/app.log",
            "bash -c 'echo hi'",
            "node server.js",
        ],
    )
    def test_ignores_commands_without_python(self, command):
        assert sut.command_invokes_python_with_buffered_stdout(command) is False


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


class TestFindStreamingAntiPatternsInCommand:
    def test_returns_all_triggered_rule_names(self):
        command = "python3 worker.py | grep ERROR | sed 's/foo/bar/'"
        problems = sut.find_streaming_anti_patterns_in_command(command)
        assert "python-without-u" in problems
        assert "grep-without-line-buffered" in problems
        assert "sed-without-u" in problems

    def test_returns_empty_list_for_clean_command(self):
        command = "tail -f /var/log/app.log | grep --line-buffered ERROR"
        assert sut.find_streaming_anti_patterns_in_command(command) == []
