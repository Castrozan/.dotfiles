import subprocess
from pathlib import Path

import pytest


GUARD = Path(__file__).resolve().parents[2] / "scripts/nh-guard"


@pytest.fixture
def argument_record(monkeypatch, tmp_path):
    record = tmp_path / "arguments"
    backend = tmp_path / "nh"
    backend.write_text(
        "#!/usr/bin/env bash\n"
        ': > "$NH_ARGUMENT_RECORD"\n'
        'for argument; do printf \'%s\\0\' "$argument" >> "$NH_ARGUMENT_RECORD"; done\n'
        "cat\n"
        "printf 'backend diagnostic\\n' >&2\n"
        "exit 37\n"
    )
    backend.chmod(0o755)
    monkeypatch.setenv("REAL_NH", str(backend))
    monkeypatch.setenv("NH_ARGUMENT_RECORD", str(record))
    return record


@pytest.mark.parametrize(
    "arguments",
    [
        ["os", "switch"],
        ["os", "switch", "/configuration with spaces"],
        ["-v", "os", "switch"],
        ["os", "--verbose", "switch"],
        ["--elevation-strategy", "sudo", "os", "switch"],
        ["os", "-e", "sudo", "switch"],
        ["--elevation-strategy=sudo", "os", "switch"],
        ["-esudo", "os", "switch"],
        ["-vqe", "sudo", "os", "switch"],
        ["os", "-ve", "sudo", "switch"],
        ["-vqe=sudo", "os", "switch"],
    ],
)
def test_switch_is_rejected_before_executing_nh(arguments, argument_record):
    result = subprocess.run(
        ["bash", str(GUARD), *arguments], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 1
    assert "Use 'rebuild'" in result.stderr
    assert not argument_record.exists()


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--help"],
        ["--version"],
        ["os", "info"],
        ["os", "build", "--help"],
        ["search", "packages", "os", "switch", "--json"],
        ["search", "options", "--scope=home-manager", "programs.git.enable"],
        ["--elevation-strategy", "os", "search", "packages", "switch"],
        ["-ve", "os", "search", "packages", "switch"],
        ["home", "switch", "--help"],
        ["search", "packages", "argument with spaces", ""],
    ],
)
def test_other_commands_preserve_arguments_streams_and_status(
    arguments, argument_record
):
    result = subprocess.run(
        ["bash", str(GUARD), *arguments],
        input="input payload\n",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 37
    assert result.stdout == "input payload\n"
    assert result.stderr == "backend diagnostic\n"
    assert argument_record.read_bytes().split(b"\0")[:-1] == [
        argument.encode() for argument in arguments
    ]
