import json
import subprocess
import time

DISCORD_VOICE = "discord-voice"
COMMAND_TIMEOUT_SECONDS = 30
STATUS_TIMEOUT_SECONDS = 5
JOIN_WAIT_SECONDS = 20
POLL_SECONDS = 0.5
JOIN_A_VOICE_CHANNEL_FIRST = (
    "The avatar could not join a Discord call: join a Discord voice channel first"
)


def run_discord_voice(*arguments, timeout=COMMAND_TIMEOUT_SECONDS):
    try:
        return subprocess.run(
            [DISCORD_VOICE, *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def read_status():
    try:
        status = json.loads(run_discord_voice("status", timeout=STATUS_TIMEOUT_SECONDS))
    except ValueError:
        return None
    return status if isinstance(status, dict) and "joined" in status else None


def in_call():
    status = read_status()
    return status is not None and status.get("joined") is True


def listener_left_the_call():
    status = read_status()
    if status is None:
        return False
    return not (status["joined"] is True and status.get("listener_present") is True)


def join():
    run_discord_voice("join")
    deadline = time.monotonic() + JOIN_WAIT_SECONDS
    while not in_call():
        if time.monotonic() > deadline:
            raise TimeoutError(JOIN_A_VOICE_CHANNEL_FIRST)
        time.sleep(POLL_SECONDS)


def leave():
    run_discord_voice("leave")
