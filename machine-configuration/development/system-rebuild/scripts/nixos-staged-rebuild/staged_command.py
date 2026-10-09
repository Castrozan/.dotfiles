import os
import subprocess


def run_command(phase, command, capture_output=False):
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


def command_failure_status(error):
    return error.returncode if error.returncode >= 0 else 128 - error.returncode
