import json
import os
import subprocess
import sys
import time
from pathlib import Path

from container_commands import run_command


def cleanup_marker(policy):
    return Path(policy.state_root) / "cleanup.json"


def ensure_cleanup_running(policy):
    if not policy.virtual_machine:
        return
    result = run_command(
        [
            "/bin/launchctl",
            "kickstart",
            "-p",
            f"gui/{os.getuid()}/org.nix-community.home.devenv-container-cleanup",
        ],
        os.environ.copy(),
        capture=True,
        timeout=10,
    )
    process_identifier = int(result.stdout.strip())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        os.kill(process_identifier, 0)
        try:
            marker = json.loads(cleanup_marker(policy).read_text())
            if marker["process_identifier"] == process_identifier:
                return
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.1)
    raise ValueError("Development cleanup service did not become ready")


def watch_cleanup(policy):
    marker = cleanup_marker(policy)
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary_marker = marker.with_suffix(".tmp")
    temporary_marker.write_text(json.dumps({"process_identifier": os.getpid()}))
    temporary_marker.replace(marker)
    while True:
        try:
            run_command(
                [
                    sys.executable,
                    str(Path(__file__).with_name("devenv_container.py")),
                    "collect",
                ],
                os.environ.copy(),
                timeout=60,
                termination_grace_seconds=15,
            )
        except (OSError, subprocess.SubprocessError) as error:
            print(f"devenv-container cleanup: {error}", file=sys.stderr, flush=True)
        time.sleep(60)
