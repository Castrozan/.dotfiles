import os
import subprocess
import sys
from pathlib import Path

from test_managed_rebuild_lock import start_holder, stop_holder


def test_steward_preflight_cannot_evaluate_while_a_machine_rebuild_owns_the_lock(
    managed_rebuild_environment, tmp_path
):
    scripts = (
        Path(__file__).resolve().parents[5] / "agent-harness/harnesses/clawde/scripts"
    )
    marker = tmp_path / "unguarded-evaluation"
    fake_nix = tmp_path / "nix"
    fake_nix.write_text(f'#!/usr/bin/env bash\ntouch "{marker}"\n')
    fake_nix.chmod(0o755)
    environment = {
        **managed_rebuild_environment,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "PYTHONPATH": str(scripts),
    }
    holder = start_holder(environment, tmp_path)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from steward_rebuild import desired_system; desired_system('fixture-configuration')",
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert completed.returncode != 0
        assert "LOCKED_BY_CONCURRENT_RUN" in completed.stderr
        assert not marker.exists()
    finally:
        stop_holder(holder)
