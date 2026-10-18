import shutil
import subprocess

from herdr_pane_client import belongs_to_a_subagent
from hook_dispatch import HandlerResult


def handle(hook_input):
    if hook_input.get("hook_event_name") != "Stop" or belongs_to_a_subagent(hook_input):
        return None
    command = shutil.which("chrome-devtools")
    if command is None:
        return None
    try:
        result = subprocess.run(
            [command, "cleanup"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=25,
            check=False,
        )
        if not result.returncode:
            return None
        reason = result.stderr.strip() or "worker cleanup failed"
    except (OSError, subprocess.TimeoutExpired) as error:
        reason = str(error)
    return HandlerResult(
        decision="block",
        reason=f"Chrome DevTools cleanup failed: {reason}. Run chrome-devtools stop before completing.",
    )
