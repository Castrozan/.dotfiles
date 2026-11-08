import os
from pathlib import Path

import user_units

LISTENER_SERVICE = "avatar-listener.service"
LIVE_SERVICE = "avatar-live.service"
CAPTURE_SERVICES = (LISTENER_SERVICE, LIVE_SERVICE)


def runtime_directory():
    base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(base) / "avatar"


def capturing_services():
    return [service for service in CAPTURE_SERVICES if user_units.unit_active(service)]


def listening():
    return any(user_units.unit_active(service) for service in CAPTURE_SERVICES)
