"""Resolve user and operating system identity for the session banner."""

from __future__ import annotations

import os
import platform
from typing import Dict


def get_system_info() -> Dict[str, str]:
    info = {}

    info["user"] = os.environ.get("USER", "unknown")

    system_name = platform.system()
    if system_name == "Darwin":
        macos_version = platform.mac_ver()[0]
        info["os"] = f"macOS {macos_version}" if macos_version else "macOS"
    else:
        try:
            release = platform.freedesktop_os_release()
            info["os"] = release.get("PRETTY_NAME", release.get("NAME", "unknown"))
        except (OSError, AttributeError):
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for os_release_line in f:
                        if os_release_line.startswith("PRETTY_NAME="):
                            info["os"] = (
                                os_release_line.split("=", 1)[1].strip().strip('"')
                            )
                            break
                        elif os_release_line.startswith("NAME=") and "os" not in info:
                            info["os"] = (
                                os_release_line.split("=", 1)[1].strip().strip('"')
                            )

    return info
