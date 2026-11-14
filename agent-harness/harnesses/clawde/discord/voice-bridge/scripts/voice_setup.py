import json
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
    conversation = voice_control.request_conductor_selection(arguments.agent)
    if "error" in conversation:
        return conversation
    preferred = arguments.bot or arguments.agent or "primary"
    result = voice_control.request_join(preferred, arguments.follow_listener)
    return {**result, "conversation": conversation}


def prepare_virtual_devices():
    prepared = subprocess.run(
        ["avatar-start", "--virtual-only"], capture_output=True, text=True, timeout=65
    )
    if prepared.returncode:
        return {
            "error": "virtual_meeting_preparation_failed",
            "detail": prepared.stderr.strip(),
        }
    return json.loads(prepared.stdout)


def apply_meeting_character(character):
    if not character:
        return {}
    changed = subprocess.run(
        ["avatar-command", "character", character],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if changed.returncode:
        return {
            "error": "meeting_character_failed",
            "detail": changed.stderr.strip(),
            "runtime": "avatar.target remains active under avatar lifecycle ownership",
        }
    confirmed = subprocess.run(
        ["avatar-command", "status"], capture_output=True, text=True, timeout=15
    )
    if (
        confirmed.returncode
        or json.loads(confirmed.stdout).get("currentCharacter") != character
    ):
        return {"error": "meeting_character_not_confirmed"}
    return {}


def meeting_start(_arguments):
    state = voice_control.request_running_bridge(command="status")
    if "error" in state:
        return state
    if state["joined"]:
        return {"error": "leave_discord_before_meeting_microphone_use"}
    devices = prepare_virtual_devices()
    if "error" in devices:
        return devices
    character_result = apply_meeting_character(state["speech"]["character"])
    return {
        **devices,
        "speech": state["speech"],
        "speech_command": "avatar-command speak TEXT EMOTION mic VOICE MODEL",
        "automatic_discord_receive": False,
        **character_result,
    }
