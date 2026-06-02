#!/usr/bin/env python3
"""Cross-machine messaging for the dotfiles steward agents over SSH.

A message is a small JSON file appended to a peer's inbox directory over SSH.
No daemon, no open ports: delivery reuses the existing Tailscale mesh and the
universal ~/.ssh/id_ed25519 key that every machine already authorizes.

Peer endpoints come from a peers file (default ~/clawde/steward/peers.json):

    {
      "self": "chise",
      "remote_inbox": "clawde/steward/inbox",
      "peers": {
        "jojo": {"host": "100.127.240.60", "user": "lucas.zanoni",
                 "identity_file": "~/.ssh/id_ed25519"}
      }
    }
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SSH_OPTIONS = [
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=accept-new",
    "-o",
    "ConnectTimeout=8",
]


def peers_file_path() -> Path:
    return Path(
        os.environ.get(
            "STEWARD_PEERS_FILE", str(Path.home() / "clawde" / "steward" / "peers.json")
        )
    )


def load_peers_configuration() -> dict:
    path = peers_file_path()
    if not path.is_file():
        sys.stderr.write(f"steward-msg: peers file not found at {path}\n")
        sys.exit(2)
    return json.loads(path.read_text())


def local_inbox_directory() -> Path:
    return (
        Path(
            os.environ.get(
                "STEWARD_WORKSPACE_DIR", str(Path.home() / "clawde" / "steward")
            )
        )
        / "inbox"
    )


def ssh_target(peer: dict) -> str:
    return f"{peer['user']}@{peer['host']}"


def ssh_base_arguments(peer: dict) -> list[str]:
    identity = os.path.expanduser(peer.get("identity_file", "~/.ssh/id_ed25519"))
    return ["ssh", "-i", identity, *SSH_OPTIONS, ssh_target(peer)]


def deliver_to_peer(
    configuration: dict, peer_alias: str, text: str
) -> tuple[bool, str]:
    peers = configuration.get("peers", {})
    if peer_alias not in peers:
        return False, f"unknown peer '{peer_alias}'"
    peer = peers[peer_alias]
    remote_inbox = configuration.get("remote_inbox", "clawde/steward/inbox")
    sender = configuration.get("self", "unknown")
    message = {
        "from": sender,
        "to": peer_alias,
        "sent_unix": int(time.time()),
        "text": text,
    }
    filename = f"{int(time.time() * 1000)}-from-{sender}.json"
    remote_command = (
        f'umask 077; mkdir -p "$HOME/{remote_inbox}"; '
        f'cat > "$HOME/{remote_inbox}/{filename}"'
    )
    try:
        completed = subprocess.run(
            [*ssh_base_arguments(peer), remote_command],
            input=json.dumps(message),
            text=True,
            capture_output=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False, "ssh timeout"
    if completed.returncode != 0:
        return False, completed.stderr.strip() or f"ssh exit {completed.returncode}"
    return True, filename


def command_send(configuration: dict, arguments: argparse.Namespace) -> int:
    ok, detail = deliver_to_peer(configuration, arguments.peer, arguments.text)
    status = "delivered" if ok else "failed"
    print(json.dumps({"peer": arguments.peer, "status": status, "detail": detail}))
    return 0 if ok else 1


def command_broadcast(configuration: dict, arguments: argparse.Namespace) -> int:
    results = []
    all_ok = True
    for peer_alias in sorted(configuration.get("peers", {})):
        ok, detail = deliver_to_peer(configuration, peer_alias, arguments.text)
        all_ok = all_ok and ok
        results.append(
            {
                "peer": peer_alias,
                "status": "delivered" if ok else "failed",
                "detail": detail,
            }
        )
    print(json.dumps({"results": results}, indent=2))
    return 0 if all_ok else 1


def command_peers(configuration: dict, arguments: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "self": configuration.get("self"),
                "peers": sorted(configuration.get("peers", {})),
            },
            indent=2,
        )
    )
    return 0


def command_inbox(configuration: dict, arguments: argparse.Namespace) -> int:
    inbox = local_inbox_directory()
    messages = []
    if inbox.is_dir():
        for entry in sorted(inbox.glob("*.json")):
            try:
                messages.append(json.loads(entry.read_text()) | {"file": entry.name})
            except json.JSONDecodeError:
                messages.append({"file": entry.name, "parse_error": True})
    print(json.dumps({"count": len(messages), "messages": messages}, indent=2))
    if arguments.drain and inbox.is_dir():
        read_directory = inbox / "read"
        read_directory.mkdir(parents=True, exist_ok=True)
        for entry in inbox.glob("*.json"):
            entry.rename(read_directory / entry.name)
    return 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="steward-msg")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send = subparsers.add_parser("send", help="send a message to one peer")
    send.add_argument("peer")
    send.add_argument("text")
    send.set_defaults(handler=command_send)

    broadcast = subparsers.add_parser("broadcast", help="send a message to all peers")
    broadcast.add_argument("text")
    broadcast.set_defaults(handler=command_broadcast)

    peers = subparsers.add_parser("peers", help="list configured peers")
    peers.set_defaults(handler=command_peers)

    inbox = subparsers.add_parser("inbox", help="show local inbox messages")
    inbox.add_argument(
        "--drain", action="store_true", help="move shown messages to inbox/read/"
    )
    inbox.set_defaults(handler=command_inbox)

    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    configuration = load_peers_configuration()
    return arguments.handler(configuration, arguments)


if __name__ == "__main__":
    sys.exit(main())
