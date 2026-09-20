from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Sequence

SERVICE_LABEL_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
LAUNCHD_CONTROLLER = "launchd"
SYSTEMD_CONTROLLER = "systemd"
SERVICE_CONTROLLERS = (LAUNCHD_CONTROLLER, SYSTEMD_CONTROLLER)


def validated_service_label(service_label: str) -> str:
    if not SERVICE_LABEL_PATTERN.match(service_label):
        raise ValueError(f"{service_label!r} is not a usable service label")
    return service_label


def launchd_service_target(service_label: str) -> str:
    return f"gui/{os.getuid()}/{validated_service_label(service_label)}"


def start_command_for(service_controller: str, service_label: str) -> list[str]:
    if service_controller == LAUNCHD_CONTROLLER:
        return ["launchctl", "kickstart", launchd_service_target(service_label)]
    return ["systemctl", "--user", "start", validated_service_label(service_label)]


def stop_command_for(service_controller: str, service_label: str) -> list[str]:
    if service_controller == LAUNCHD_CONTROLLER:
        return ["launchctl", "kill", "SIGTERM", launchd_service_target(service_label)]
    return ["systemctl", "--user", "stop", validated_service_label(service_label)]


def run_service_command(command: Sequence[str]) -> None:
    if not command:
        return
    try:
        subprocess.run(list(command), check=False)
    except OSError:
        pass
