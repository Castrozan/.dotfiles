import json
import subprocess

AUTHENTICATION_TIMEOUT_SECONDS = 15


def claude_authentication_failure() -> str | None:
    try:
        completed = subprocess.run(
            ["claude", "auth", "status", "--json"],
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
    if not isinstance(status, dict):
        return "Claude authentication status did not return an object"
    if status.get("loggedIn") is False:
        return "Claude is not authenticated; this scenario cannot run"
    if completed.returncode != 0 or status.get("loggedIn") is not True:
        return "Claude authentication status did not confirm access"
    return None
