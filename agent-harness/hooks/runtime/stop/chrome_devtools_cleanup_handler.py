import shutil
import subprocess

ATTACHED_WORKER_IDLE_EXPIRY_SECONDS = 1800

from herdr_pane_client import belongs_to_a_subagent
from hook_dispatch import HandlerResult


def cleanup_failure_reason(command):
    try:
        result = subprocess.run(
            [command, "cleanup", "--keep-attached-for", str(ATTACHED_WORKER_IDLE_EXPIRY_SECONDS)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=25,
            check=False,
        )
        if not result.returncode:
            return None
        return result.stderr.strip() or "worker cleanup failed"
    except (OSError, subprocess.TimeoutExpired) as error:
        return str(error)


def handle(hook_input):
    if hook_input.get("hook_event_name") != "Stop" or belongs_to_a_subagent(hook_input):
        return None
    command = shutil.which("chrome-devtools")
    if command is None:
        return None
    if reason := cleanup_failure_reason(command):
        return HandlerResult(
            decision="block",
            reason=f"Chrome DevTools cleanup failed: {reason}. Run chrome-devtools stop before completing.",
        )
    return None
