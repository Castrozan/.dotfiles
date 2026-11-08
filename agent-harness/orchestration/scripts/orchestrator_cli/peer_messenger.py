from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

A2A_COMMAND_TIMEOUT_SECONDS = 30


class PeerMessageFailure(Exception):
    pass


def run_a2a(*arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["a2a", *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=A2A_COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as failure:
        raise PeerMessageFailure(f"a2a {arguments[0]}: {failure}") from failure
    if completed.returncode != 0:
        raise PeerMessageFailure(
            completed.stderr.strip()
            or f"a2a {arguments[0]} exited {completed.returncode}"
        )
    return completed.stdout.strip()


def sender_name(explicit_sender: str | None) -> str:
    return run_a2a(
        "whoami", *(["--sender", explicit_sender] if explicit_sender else [])
    )


def notify_peer(target: str, sender: str, text: str) -> None:
    run_a2a("notify", target, text, "--sender", sender)


def notify_after_save(
    resolve_sender: Callable[[], str], target: str, text: str, saved_path: Path
) -> int:
    try:
        notify_peer(target, resolve_sender(), text)
    except PeerMessageFailure as failure:
        print(
            f"orchestrator: {saved_path} is saved but {target} was not notified: {failure}",
            file=sys.stderr,
        )
        return 1
    return 0
