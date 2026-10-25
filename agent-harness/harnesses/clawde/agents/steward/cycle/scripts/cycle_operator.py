import re
from pathlib import Path

from cycle_commands import CommandRunner
from cycle_configuration import CycleConfiguration
from cycle_records import read_record

OPERATOR_IDLE_SECONDS = 15 * 60
HID_IDLE_TIME_PATTERN = re.compile(r'"HIDIdleTime" = (\d+)')
HID_QUERY_TIMEOUT_SECONDS = 15


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


def human_interface_idle_seconds(runner: CommandRunner, directory: Path) -> float:
    result = runner.run(
        ["ioreg", "-c", "IOHIDSystem", "-d", "4"], directory, HID_QUERY_TIMEOUT_SECONDS
    )
    match = HID_IDLE_TIME_PATTERN.search(result.output)
    return int(match.group(1)) / 1e9 if match else 0


def operator_idle(configuration: CycleConfiguration, runner: CommandRunner) -> bool:
    if not configuration.operator_idle_required:
        return True
    if configuration.idle_marker is not None:
        return configuration.idle_marker.exists()
    idle_seconds = human_interface_idle_seconds(runner, configuration.state_directory)
    return idle_seconds >= OPERATOR_IDLE_SECONDS
