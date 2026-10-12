import os
import subprocess
from pathlib import Path

import pytest


HERDR_AUTOSTART_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "program-configuration"
    / "bash_herdr_autostart.sh"
)


@pytest.mark.parametrize(
    ("terminal_environment", "expected_output"),
    [
        ({"TERM_PROGRAM": "cockpit", "HERDR_ENV": "1"}, ""),
        ({"TERM_PROGRAM": "WezTerm"}, "herdr-started"),
    ],
)
def test_managed_browser_terminal_keeps_shell_and_normal_terminal_starts_herdr(
    terminal_environment, expected_output
):
    completed = subprocess.run(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-i",
            "-c",
            'herdr() { printf herdr-started; }; source "$1"',
            "shell-startup-test",
            str(HERDR_AUTOSTART_SCRIPT),
        ],
        env={
            "PATH": os.environ["PATH"],
            "TERM": "xterm-256color",
            **terminal_environment,
        },
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout == expected_output
