from __future__ import annotations

import argparse
import ipaddress
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from holder_registry import HolderRegistry

LISTEN_POLL_INTERVAL_SECONDS = 0.1
PROBE_CONNECTION_TIMEOUT_SECONDS = 0.5
SIGNALS_FORWARDED_TO_CHILD = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)


def loopback_probe_target(listen_address: str, listen_port: int) -> tuple[str, int]:
    address = ipaddress.ip_address(listen_address)
    if not address.is_loopback:
        raise ValueError(f"{listen_address} is not a loopback address")
    if not 1 <= listen_port <= 65535:
        raise ValueError(f"{listen_port} is not a usable port")
    return str(address), listen_port


def service_is_listening(listen_address: str, listen_port: int) -> bool:
    try:
        probe_target = loopback_probe_target(listen_address, listen_port)
    except ValueError:
        return False

    try:
        with socket.create_connection(
            probe_target, PROBE_CONNECTION_TIMEOUT_SECONDS
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


def launchd_service_target(service_label: str) -> str:
    return f"gui/{os.getuid()}/{service_label}"


def start_command_for(service_controller: str, service_label: str) -> list[str]:
    if service_controller == "launchd":
        return ["launchctl", "kickstart", launchd_service_target(service_label)]
    return ["systemctl", "--user", "start", service_label]


def stop_command_for(service_controller: str, service_label: str) -> list[str]:
    if service_controller == "launchd":
        return ["launchctl", "kill", "SIGTERM", launchd_service_target(service_label)]
    return ["systemctl", "--user", "stop", service_label]


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
    parser.add_argument("--service-controller", required=True, choices=["launchd", "systemd"])
    parser.add_argument("--service-label", required=True)
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
        start_command_for(arguments.service_controller, arguments.service_label),
        stop_command_for(arguments.service_controller, arguments.service_label),
        arguments.startup_timeout_seconds,
        arguments.unavailable_message,
        child_arguments,
    )


if __name__ == "__main__":
    sys.exit(main())
