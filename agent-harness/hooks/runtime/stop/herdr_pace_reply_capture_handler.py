import json
import shutil
import subprocess

from herdr_pane_client import belongs_to_a_subagent, running_inside_a_herdr_pane


def handle(hook_input: dict):
    if hook_input.get("hook_event_name") != "Stop":
        return None
    if belongs_to_a_subagent(hook_input) or not running_inside_a_herdr_pane():
        return None
    command = shutil.which("herdr-pace")
    if command is None:
        return None
    capture_fields = (
        "hook_event_name",
        "session_id",
        "transcript_path",
        "reply_text",
        "last_assistant_message",
    )
    payload = {
        field: hook_input[field] for field in capture_fields if field in hook_input
    }
    try:
        subprocess.run(
            [command, "capture"],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=0.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None
