import json
import shutil
import subprocess

from herdr_pane_client import belongs_to_a_subagent, running_inside_a_herdr_pane


def _capture_payload(hook_input):
    capture_fields = (
        "hook_event_name",
        "session_id",
        "transcript_path",
        "reply_text",
        "last_assistant_message",
    )
    return {field: hook_input[field] for field in capture_fields if field in hook_input}


def _run_capture(command, payload):
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


def handle(hook_input: dict):
    if hook_input.get("hook_event_name") != "Stop":
        return None
    if belongs_to_a_subagent(hook_input) or not running_inside_a_herdr_pane():
        return None
    command = shutil.which("herdr-pace")
    if command is None:
        return None
    payload = _capture_payload(hook_input)
    _run_capture(command, payload)
    return None
