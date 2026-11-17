import os
import re
import subprocess
import time

LAUNCHCTL = "/bin/launchctl"
CONVERSATION_AGENT = "com.dotfiles.avatar-conversation"
LIVE_AGENT = "com.dotfiles.avatar-live"
CONVERSATION_TARGET = "avatar-conversation.target"
AGENT_BY_UNIT = {
    CONVERSATION_TARGET: CONVERSATION_AGENT,
    "avatar-listener.service": CONVERSATION_AGENT,
    "avatar-live.service": LIVE_AGENT,
    "avatar-control-server.service": "com.dotfiles.avatar-control",
    "avatar-renderer.service": "com.dotfiles.avatar-renderer",
}
AGENTS_KEEPING_UNIT_ACTIVE = {CONVERSATION_TARGET: (CONVERSATION_AGENT, LIVE_AGENT)}
RUNNING = re.compile(r"^\tstate = running$", re.MULTILINE)
COMMAND_TIMEOUT_SECONDS = 30
STOP_WAIT_SECONDS = 10
POLL_SECONDS = 0.1


def agent_target(agent):
    return f"gui/{os.getuid()}/{agent}"


def service_target(unit):
    return agent_target(AGENT_BY_UNIT[unit])


def launchctl(*arguments, check=False):
    return subprocess.run(
        [LAUNCHCTL, *arguments],
        capture_output=True,
        text=True,
        check=check,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def agent_running(agent):
    return bool(RUNNING.search(launchctl("print", agent_target(agent)).stdout))


def unit_active(unit):
    if unit not in AGENT_BY_UNIT:
        return False
    agents = AGENTS_KEEPING_UNIT_ACTIVE.get(unit, (AGENT_BY_UNIT[unit],))
    return any(agent_running(agent) for agent in agents)


def start(unit):
    launchctl("kickstart", service_target(unit), check=True)


def stop(unit):
    launchctl("kill", "TERM", service_target(unit))
    deadline = time.monotonic() + STOP_WAIT_SECONDS
    while unit_active(unit):
        if time.monotonic() > deadline:
            raise TimeoutError(f"{AGENT_BY_UNIT[unit]} did not stop")
        time.sleep(POLL_SECONDS)
