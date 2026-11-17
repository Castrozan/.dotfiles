import subprocess

import voice_control


def meeting_runtime_active():
    meeting = subprocess.run(
        ["systemctl", "--user", "is-active", "avatar.target"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return meeting.stdout.strip() in {"active", "activating", "reloading"}


def join(arguments):
    if meeting_runtime_active():
        return {"error": "meeting_devices_active_leave_meeting_before_discord"}
    voice_control.control_bridge_service("start")
    return voice_control.request_join(
        arguments.bot or "primary", arguments.follow_listener
    )
