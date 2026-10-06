"""Resolve user and operating system identity for the session banner."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Dict


def resolve_host_identity() -> Dict[str, str]:
    host_identity_path = Path.home() / "clawde" / "host-identity.json"
    try:
        host_identity = json.loads(host_identity_path.read_text())
    except (OSError, ValueError):
        return {}

    resolved = {}
    alias = host_identity.get("alias")
    if alias:
        resolved["host"] = alias
    return resolved


def _fallback_os_release_name():
    os_description = None
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for os_release_line in f:
                if os_release_line.startswith("PRETTY_NAME="):
                    os_description = os_release_line.split("=", 1)[1].strip().strip('"')
                    break
                elif os_release_line.startswith("NAME=") and os_description is None:
                    os_description = os_release_line.split("=", 1)[1].strip().strip('"')
    return os_description


def _linux_os_description():
    try:
        release = platform.freedesktop_os_release()
        return release.get("PRETTY_NAME", release.get("NAME", "unknown"))
    except (OSError, AttributeError):
        return _fallback_os_release_name()


def get_system_info() -> Dict[str, str]:
    info = {}

    info["user"] = os.environ.get("USER", "unknown")
    info.update(resolve_host_identity())

    system_name = platform.system()
    if system_name == "Darwin":
        macos_version = platform.mac_ver()[0]
        info["os"] = f"macOS {macos_version}" if macos_version else "macOS"
    else:
        os_description = _linux_os_description()
        if os_description is not None:
            info["os"] = os_description

    return info
