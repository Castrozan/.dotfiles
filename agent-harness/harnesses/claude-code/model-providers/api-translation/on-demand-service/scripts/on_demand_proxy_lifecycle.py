from __future__ import annotations

import argparse
import errno
import json
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

LOCK_ACQUISITION_TIMEOUT_SECONDS = 10
LOCK_RETRY_INTERVAL_SECONDS = 0.05
LISTEN_POLL_INTERVAL_SECONDS = 0.1
PROBE_CONNECTION_TIMEOUT_SECONDS = 0.5
SIGNALS_FORWARDED_TO_CHILD = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)


class HolderRegistry:
    def __init__(self, registry_directory: Path) -> None:
        self.registry_directory = registry_directory
        self.holders_path = registry_directory / "holders"
        self.adopted_marker_path = registry_directory / "started-outside-the-launchers"
        self.lock_path = registry_directory / "lock"

    def __enter__(self) -> "HolderRegistry":
        self.registry_directory.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_ACQUISITION_TIMEOUT_SECONDS
        while True:
            try:
                os.mkdir(self.lock_path)
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    self._break_stale_lock()
                    continue
                time.sleep(LOCK_RETRY_INTERVAL_SECONDS)

    def __exit__(self, *_exception_details: object) -> None:
        try:
            os.rmdir(self.lock_path)
        except OSError:
            pass

    def _break_stale_lock(self) -> None:
        try:
            os.rmdir(self.lock_path)
        except OSError:
            pass

    def live_holders(self) -> list[int]:
        try:
            recorded = self.holders_path.read_text().split()
        except OSError:
            return []

        return [
            process_id
            for process_id in (int(entry) for entry in recorded if entry.isdigit())
            if process_is_alive(process_id)
        ]

    def write_holders(self, holders: Sequence[int]) -> None:
        self.holders_path.write_text(
            "".join(f"{process_id}\n" for process_id in holders)
        )

    def mark_adopted(self) -> None:
        self.adopted_marker_path.touch()

    def clear_adoption(self) -> None:
        self.adopted_marker_path.unlink(missing_ok=True)

    def was_adopted(self) -> bool:
        return self.adopted_marker_path.exists()


def process_is_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except OSError as probe_failure:
        return probe_failure.errno == errno.EPERM
    return True


def service_is_listening(listen_address: str, listen_port: int) -> bool:
    try:
        with socket.create_connection(
            (listen_address, listen_port), PROBE_CONNECTION_TIMEOUT_SECONDS
        ):
            return True
    except OSError:
        return False


def wait_until_listening(
    listen_address: str, listen_port: int, timeout_seconds: float
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if service_is_listening(listen_address, listen_port):
            return True
        time.sleep(LISTEN_POLL_INTERVAL_SECONDS)
    return service_is_listening(listen_address, listen_port)


def run_service_command(command: Sequence[str]) -> None:
    if not command:
        return
    subprocess.run(command, check=False)


def acquire_service(
    registry_directory: Path,
    listen_address: str,
    listen_port: int,
    start_command: Sequence[str],
) -> None:
    with HolderRegistry(registry_directory) as registry:
        holders = registry.live_holders()
        if not holders:
            if service_is_listening(listen_address, listen_port):
                registry.mark_adopted()
            else:
                registry.clear_adoption()
                run_service_command(start_command)
        registry.write_holders([*holders, os.getpid()])


def release_service(
    registry_directory: Path, stop_command: Sequence[str]
) -> None:
    with HolderRegistry(registry_directory) as registry:
        remaining = [
            process_id
            for process_id in registry.live_holders()
            if process_id != os.getpid()
        ]
        registry.write_holders(remaining)
        if remaining or registry.was_adopted():
            return
        run_service_command(stop_command)


def run_child_forwarding_signals(child_arguments: Sequence[str]) -> int:
    child_process = subprocess.Popen(child_arguments)

    def forward_signal(received_signal: int, _frame: object) -> None:
        try:
            child_process.send_signal(received_signal)
        except OSError:
            pass

    previous_handlers = {
        forwarded: signal.signal(forwarded, forward_signal)
        for forwarded in SIGNALS_FORWARDED_TO_CHILD
    }
    try:
        return child_process.wait()
    finally:
        for forwarded, previous_handler in previous_handlers.items():
            signal.signal(forwarded, previous_handler)


def run_with_on_demand_service(
    registry_directory: Path,
    listen_address: str,
    listen_port: int,
    start_command: Sequence[str],
    stop_command: Sequence[str],
    startup_timeout_seconds: float,
    unavailable_message: str,
    child_arguments: Sequence[str],
) -> int:
    acquire_service(registry_directory, listen_address, listen_port, start_command)
    try:
        if not wait_until_listening(
            listen_address, listen_port, startup_timeout_seconds
        ):
            print(unavailable_message, file=sys.stderr)
        return run_child_forwarding_signals(child_arguments)
    finally:
        release_service(registry_directory, stop_command)


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-directory", required=True, type=Path)
    parser.add_argument("--listen-address", required=True)
    parser.add_argument("--listen-port", required=True, type=int)
    parser.add_argument("--start-command", required=True)
    parser.add_argument("--stop-command", required=True)
    parser.add_argument("--startup-timeout-seconds", required=True, type=float)
    parser.add_argument("--unavailable-message", required=True)
    parser.add_argument("child_arguments", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    child_arguments = list(arguments.child_arguments)
    if child_arguments and child_arguments[0] == "--":
        child_arguments = child_arguments[1:]
    if not child_arguments:
        return 2

    return run_with_on_demand_service(
        arguments.registry_directory,
        arguments.listen_address,
        arguments.listen_port,
        json.loads(arguments.start_command),
        json.loads(arguments.stop_command),
        arguments.startup_timeout_seconds,
        arguments.unavailable_message,
        child_arguments,
    )


if __name__ == "__main__":
    sys.exit(main())
