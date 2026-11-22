import json
import subprocess
import time

DISCORD_VOICE = "discord-voice"
COMMAND_TIMEOUT_SECONDS = 30
JOIN_TIMEOUT_SECONDS = 75
STATUS_TIMEOUT_SECONDS = 5
JOIN_WAIT_SECONDS = 20
POLL_SECONDS = 0.5
COULD_NOT_JOIN = "The avatar could not join a Discord call"
JOIN_REFUSALS = {
    "listener_not_in_allowed_voice_channel": "join a Discord voice channel first",
    "bridge_not_ready": "the Discord bots are not connected yet, see discord-voice status",
    "no_eligible_available_bot_for_listener": "no Discord bot is free to join your channel, see discord-voice status",
    "bridge_not_running": "the Discord bridge is not running",
    "bridge_did_not_start": "the Discord bridge did not start",
}


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


def parsed_reply(stdout):
    try:
        return json.loads(stdout)
    except ValueError:
        return None


def read_status():
    status = parsed_reply(run_discord_voice("status", timeout=STATUS_TIMEOUT_SECONDS))
    return status if isinstance(status, dict) and "joined" in status else None


def join_refusal(reply):
    if not isinstance(reply, dict):
        return "the Discord bridge did not answer"
    error = reply.get("error")
    if error is None:
        return None
    return JOIN_REFUSALS.get(error, f"the Discord bridge refused with {error}")


def in_call():
    status = read_status()
    return status is not None and status.get("joined") is True


def listener_left_the_call():
    status = read_status()
    if status is None:
        return False
    return not (status["joined"] is True and status.get("listener_present") is True)


def join():
    refusal = join_refusal(
        parsed_reply(run_discord_voice("join", timeout=JOIN_TIMEOUT_SECONDS))
    )
    if refusal is not None:
        raise RuntimeError(f"{COULD_NOT_JOIN}: {refusal}")
    deadline = time.monotonic() + JOIN_WAIT_SECONDS
    while not in_call():
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"{COULD_NOT_JOIN}: the Discord bridge did not join in time"
            )
        time.sleep(POLL_SECONDS)


def leave():
    run_discord_voice("leave")
