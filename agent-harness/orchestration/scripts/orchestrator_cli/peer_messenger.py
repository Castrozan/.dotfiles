from __future__ import annotations

import shlex
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

A2A_COMMAND_TIMEOUT_SECONDS = 30


class PeerMessageFailure(Exception):
    pass


@dataclass(frozen=True)
class PeerAddress:
    target: str
    host: str | None = None

    def __str__(self) -> str:
        return self.target if self.host is None else f"{self.target} on {self.host}"


def requester_address(record: dict) -> PeerAddress:
    return PeerAddress(
        record.get("requester_pane") or record["requester"],
        record.get("requester_host"),
    )


def a2a_command_line(arguments: tuple[str, ...], host: str | None) -> list[str]:
    command = ["a2a", *arguments]
    if host is None:
        return command
    return ["ssh", "-o", "BatchMode=yes", host, shlex.join(command)]


def run_a2a(*arguments: str, host: str | None = None) -> str:
    try:
        completed = subprocess.run(
            a2a_command_line(arguments, host),
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


def copy_file_to_host(path: Path, host: str) -> None:
    remote_command = (
        f"mkdir -p {shlex.quote(str(path.parent))} && cat > {shlex.quote(str(path))}"
    )
    try:
        completed = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", host, remote_command],
            input=path.read_bytes(),
            capture_output=True,
            check=False,
            timeout=A2A_COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as failure:
        raise PeerMessageFailure(f"copying {path} to {host}: {failure}") from failure
    if completed.returncode != 0:
        raise PeerMessageFailure(
            f"copying {path} to {host}: {completed.stderr.decode().strip()}"
        )


def notify_peer(address: PeerAddress, sender: str, text: str) -> None:
    run_a2a("notify", address.target, text, "--sender", sender, host=address.host)


def notify_after_save(
    resolve_sender: Callable[[], str],
    address: PeerAddress,
    text: str,
    saved_path: Path,
) -> int:
    try:
        notify_peer(address, resolve_sender(), text)
    except PeerMessageFailure as failure:
        print(
            f"orchestrator: {saved_path} is saved but {address} was not notified: {failure}",
            file=sys.stderr,
        )
        return 1
    return 0
