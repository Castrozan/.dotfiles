import subprocess
import sys
from pathlib import Path

import pytest

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import command_runner


def test_build_command_environment_prepends_system_directories(monkeypatch):
    monkeypatch.setenv("PATH", "/sentinel/existing")
    monkeypatch.setenv("USER", "tester")
    search_path_entries = command_runner.build_command_environment()["PATH"].split(":")
    assert search_path_entries[0] == "/usr/bin"
    assert "/etc/profiles/per-user/tester/bin" in search_path_entries
    assert search_path_entries[-1] == "/sentinel/existing"


def test_build_command_environment_omits_empty_existing_path(monkeypatch):
    monkeypatch.setenv("PATH", "")
    search_path_entries = command_runner.build_command_environment()["PATH"].split(":")
    assert "" not in search_path_entries


def test_run_command_capturing_stdout_returns_stdout():
    assert (
        command_runner.run_command_capturing_stdout(["echo", "hello"]).strip()
        == "hello"
    )


def test_run_command_capturing_stdout_raises_on_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        command_runner.run_command_capturing_stdout(["sleep", "5"], timeout_seconds=0.1)
