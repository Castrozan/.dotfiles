import os
import signal
import subprocess
import sys
from unittest.mock import Mock

import pytest

import container_commands


def test_timeout_terminates_and_then_kills_the_entire_command_group(monkeypatch):
    process = Mock(pid=100, returncode=-9)
    timeout = subprocess.TimeoutExpired(["command"], 1)
    process.communicate.side_effect = [timeout, timeout, (None, None)]
    popen = Mock(return_value=process)
    kill_group = Mock()
    monkeypatch.setattr(container_commands.subprocess, "Popen", popen)
    monkeypatch.setattr(container_commands.os, "killpg", kill_group)
    with pytest.raises(subprocess.TimeoutExpired):
        container_commands.run_command(["command"], {}, timeout=1)
    assert popen.call_args.kwargs["start_new_session"] is True
    assert kill_group.call_args_list[0].args == (100, signal.SIGTERM)
    assert kill_group.call_args_list[1].args == (100, signal.SIGKILL)


def test_preserve_command_exit_status_when_check_is_disabled(monkeypatch):
    process = Mock(returncode=37)
    process.communicate.return_value = ("", "")
    monkeypatch.setattr(
        container_commands.subprocess, "Popen", Mock(return_value=process)
    )
    result = container_commands.run_command(["command"], {}, check=False)
    assert result.returncode == 37


def test_interactive_command_keeps_its_controlling_terminal(monkeypatch):
    process = Mock(returncode=0)
    process.communicate.return_value = (None, None)
    popen = Mock(return_value=process)
    monkeypatch.setattr(container_commands.subprocess, "Popen", popen)
    container_commands.run_command(["command"], {}, interactive=True)
    assert popen.call_args.kwargs["start_new_session"] is False


def test_deadline_reaps_a_nested_helper_that_ignores_termination(tmp_path):
    marker = tmp_path / "child-process"
    helper = (
        "import os, signal, time; from pathlib import Path; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        f"Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    parent = (
        "import os, signal, sys; "
        "from container_commands import interrupt_command, run_command; "
        "signal.signal(signal.SIGTERM, interrupt_command); "
        f"run_command([sys.executable, '-c', {helper!r}], os.environ.copy())"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(container_commands.__file__.rsplit("/", 1)[0])
    with pytest.raises(subprocess.TimeoutExpired):
        container_commands.run_command(
            [sys.executable, "-c", parent],
            environment,
            timeout=2,
            termination_grace_seconds=15,
        )
    with pytest.raises(ProcessLookupError):
        os.kill(int(marker.read_text()), 0)
