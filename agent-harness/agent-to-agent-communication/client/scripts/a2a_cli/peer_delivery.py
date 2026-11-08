from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from .peer_identity import with_peer_identities
from .peer_transport import (
    PeerRequestFailure,
    notify_peer,
    read_agent_directory,
    resolve_peer_endpoint,
)
from .sender_identity import resolve_sender_name, validated_sender_name


def sender_and_directory(arguments: argparse.Namespace) -> tuple[str, dict]:
    agent_directory = with_peer_identities(read_agent_directory(arguments.daemon))
    if arguments.sender:
        return validated_sender_name(arguments.sender), agent_directory
    return resolve_sender_name(agent_directory), agent_directory


def notify_after_save(
    resolve_sender: Callable[[], tuple[str, dict]],
    target: str,
    text: str,
    saved_path: Path,
) -> int:
    try:
        sender, agent_directory = resolve_sender()
        notify_peer(resolve_peer_endpoint(agent_directory, target), sender, text)
    except PeerRequestFailure as failure:
        print(
            f"a2a: {saved_path} is saved but {target} was not notified: {failure}",
            file=sys.stderr,
        )
        return 1
    return 0
