from pathlib import Path

from cycle_records import read_record


def peer_names(peers_file: Path) -> set[str]:
    peers = (read_record(peers_file) or {}).get("peers", {})
    return set(peers) if isinstance(peers, dict) else set()


def unread_local_messages(inbox_directory: Path, peers_file: Path) -> tuple[str, ...]:
    peers = peer_names(peers_file)
    return tuple(
        str(message)
        for message in sorted(inbox_directory.glob("*.json"))
        if (read_record(message) or {}).get("from") not in peers
    )
