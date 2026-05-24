import pytest

import monitor_streaming_pattern_validator as sut


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
