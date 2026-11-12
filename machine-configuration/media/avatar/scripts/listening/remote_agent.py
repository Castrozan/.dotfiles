import dataclasses
import json
import re
import shlex
import subprocess

HOST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*")
LISTING_TIMEOUT_SECONDS = 20
REACH_HOST = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


@dataclasses.dataclass(frozen=True)
class AgentPane:
    host: str | None
    pane: str | None


def parse(text):
    host, _, pane = text.partition(":")
    if not HOST_NAME.fullmatch(host) or not pane:
        raise ValueError(f"{text!r} is not HOST:PANE")
    return AgentPane(host, pane)


def on_host(host, command):
    if host is None:
        return command
    return [*REACH_HOST, host, shlex.join(command)]


def servant_at(agent):
    listing = subprocess.run(
        on_host(agent.host, ["a2a", "list", "--json"]),
        capture_output=True,
        text=True,
        check=True,
        timeout=LISTING_TIMEOUT_SECONDS,
    )
    for session in json.loads(listing.stdout).values():
        if session.get("paneId") == agent.pane:
            return session.get("servant")
    return None
