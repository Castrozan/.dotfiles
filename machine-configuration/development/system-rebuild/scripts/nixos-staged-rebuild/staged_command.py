import os
import subprocess
import json
import sys
import tempfile
from pathlib import Path

from memory_records import append_record


def run_command(phase, command, capture_output=False):
    if os.environ.get("REBUILD_MEMORY_RECORDS"):
        return run_recorded_command(phase, command, capture_output)
    timed_command = [
        os.environ["REBUILD_COMMAND_TIME"],
        "-f",
        f"phase={phase} wall_seconds=%e peak_rss_kib=%M exit_status=%x",
        *map(str, command),
    ]
    completed = subprocess.run(
        timed_command,
        stdout=subprocess.PIPE if capture_output else None,
        text=True,
        check=True,
    )
    return completed.stdout.strip() if capture_output else None


def run_recorded_command(phase, command, capture_output):
    with tempfile.TemporaryDirectory(prefix="rebuild-command-memory-") as directory:
        resource_path = Path(directory) / "resources.json"
        timed_command = [
            os.environ["REBUILD_COMMAND_TIME"],
            "-f",
            '{"wall_seconds":%e,"peak_rss_kib":%M}',
            "--quiet",
            "--output",
            str(resource_path),
            *map(str, command),
        ]
        completed = subprocess.run(
            timed_command,
            stdout=subprocess.PIPE if capture_output else None,
            text=True,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
        measurement = json.loads(resource_path.read_text())
    measurement.update(phase=phase, exit_status=completed.returncode)
    append_record(measurement)
    print(
        f"phase={phase} wall_seconds={measurement['wall_seconds']:.2f} "
        f"peak_rss_kib={measurement['peak_rss_kib']} exit_status={completed.returncode}",
        file=sys.stderr,
    )
    completed.check_returncode()
    return completed.stdout.strip() if capture_output else None


def command_failure_status(error):
    return error.returncode if error.returncode >= 0 else 128 - error.returncode
