import json
import subprocess
import time

DISCORD_VOICE = "discord-voice"
COMMAND_TIMEOUT_SECONDS = 30
JOIN_WAIT_SECONDS = 20
POLL_SECONDS = 0.5
JOIN_A_VOICE_CHANNEL_FIRST = (
    "The avatar could not join a Discord call: join a Discord voice channel first"
)


def run_discord_voice(*arguments):
    try:
        return subprocess.run(
            [DISCORD_VOICE, *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def in_call():
    try:
        return json.loads(run_discord_voice("status")).get("joined") is True
    except (ValueError, AttributeError):
        return False


def join():
    run_discord_voice("join", "--follow-listener")
    deadline = time.monotonic() + JOIN_WAIT_SECONDS
    while not in_call():
        if time.monotonic() > deadline:
            raise TimeoutError(JOIN_A_VOICE_CHANNEL_FIRST)
        time.sleep(POLL_SECONDS)


def leave():
    run_discord_voice("leave")
