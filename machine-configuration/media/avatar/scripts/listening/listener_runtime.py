import os
from pathlib import Path

import user_units

LISTENER_SERVICE = "avatar-listener.service"


def runtime_directory():
    base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(base) / "avatar"


def listening():
    return user_units.unit_active(LISTENER_SERVICE)
