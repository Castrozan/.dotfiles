import json
import subprocess
from pathlib import Path

AUTHENTICATION_TIMEOUT_SECONDS = 15


def claude_authentication_failure(workspace_directory: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["claude", "auth", "status", "--json"],
            cwd=workspace_directory,
            capture_output=True,
            text=True,
            timeout=AUTHENTICATION_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "Claude authentication status could not be checked"
    try:
        status = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        return "Claude authentication status did not return valid JSON"
    return _authentication_status_failure(status, completed.returncode)


def _authentication_status_failure(status, returncode: int) -> str | None:
    if not isinstance(status, dict):
        return "Claude authentication status did not return an object"
    if status.get("loggedIn") is False:
        return "Claude is not authenticated; this scenario cannot run"
    if returncode != 0 or status.get("loggedIn") is not True:
        return "Claude authentication status did not confirm access"
    return None
