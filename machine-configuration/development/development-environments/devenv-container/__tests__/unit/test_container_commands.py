import signal
import subprocess
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
