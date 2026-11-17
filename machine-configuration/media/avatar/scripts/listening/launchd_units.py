import os
import re
import subprocess
import time

LAUNCHCTL = "/bin/launchctl"
CONVERSATION_AGENT = "com.dotfiles.avatar-conversation"
AGENT_BY_UNIT = {
    "avatar-conversation.target": CONVERSATION_AGENT,
    "avatar-listener.service": CONVERSATION_AGENT,
}
RUNNING = re.compile(r"^\tstate = running$", re.MULTILINE)
COMMAND_TIMEOUT_SECONDS = 30
STOP_WAIT_SECONDS = 10
POLL_SECONDS = 0.1


def service_target(unit):
    return f"gui/{os.getuid()}/{AGENT_BY_UNIT[unit]}"


def launchctl(*arguments, check=False):
    return subprocess.run(
        [LAUNCHCTL, *arguments],
        capture_output=True,
        text=True,
        check=check,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def unit_active(unit):
    if unit not in AGENT_BY_UNIT:
        return False
    return bool(RUNNING.search(launchctl("print", service_target(unit)).stdout))


def start(unit):
    launchctl("kickstart", service_target(unit), check=True)


def stop(unit):
    launchctl("kill", "TERM", service_target(unit))
    deadline = time.monotonic() + STOP_WAIT_SECONDS
    while unit_active(unit):
        if time.monotonic() > deadline:
            raise TimeoutError(f"{AGENT_BY_UNIT[unit]} did not stop")
        time.sleep(POLL_SECONDS)
