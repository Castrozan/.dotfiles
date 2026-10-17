import os
import subprocess
import sys
from pathlib import Path

import pytest

EVALUATIONS_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("tier", ["integration", "e2e"])
def test_unauthenticated_claude_fails_without_starting_a_session(tmp_path, tier):
    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    launch_marker = tmp_path / "launched"
    claude = binary_directory / "claude"
    claude.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        "if sys.argv[1:3] == ['auth', 'status']:\n"
        " print(json.dumps({'loggedIn': False, 'authMethod': 'none'}))\n"
        " sys.exit(1)\n"
        f"pathlib.Path({str(launch_marker)!r}).write_text('launched')\n"
        "sys.exit(1)\n"
    )
    claude.chmod(0o755)
    herdr = binary_directory / "herdr"
    herdr.write_text(f"#!{sys.executable}\nimport sys\nsys.exit(1)\n")
    herdr.chmod(0o755)
    scenario_name = {
        "integration": "no_comments_in_code",
        "e2e": "formatting_runs_after_python_edit",
    }[tier]

    completed = subprocess.run(
        [
            sys.executable,
            str(EVALUATIONS_ROOT / tier / f"run-{tier}-tests.py"),
            "--scenario",
            scenario_name,
        ],
        env={
            **os.environ,
            "PATH": str(binary_directory) + os.pathsep + os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 1
    assert "Claude is not authenticated" in completed.stdout
    assert "Passed: 0/1" in completed.stdout
    assert not launch_marker.exists()
