import os
import sys
from pathlib import Path

import user_units

LISTENER_SERVICE = "avatar-listener.service"
LIVE_SERVICE = "avatar-live.service"
CAPTURE_SERVICES = (LISTENER_SERVICE, LIVE_SERVICE)
MAC_RUNTIME_DIRECTORY = "Library/Caches/avatar"


def runtime_directory():
    if sys.platform == "darwin":
        return Path.home() / MAC_RUNTIME_DIRECTORY
    base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(base) / "avatar"


def capturing_services():
    return [service for service in CAPTURE_SERVICES if user_units.unit_active(service)]


def listening():
    return any(user_units.unit_active(service) for service in CAPTURE_SERVICES)
