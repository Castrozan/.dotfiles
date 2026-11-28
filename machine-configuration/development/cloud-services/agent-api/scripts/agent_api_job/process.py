import subprocess

COMMAND_TIMEOUT_SECONDS = 30


def run_command(arguments):
    try:
        return subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(arguments, 1, "", "")
