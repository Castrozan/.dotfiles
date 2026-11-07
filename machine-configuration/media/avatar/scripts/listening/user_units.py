import subprocess
import time

SYSTEMD_UNREACHABLE = 1
UNREACHABLE_RETRY_SECONDS = 30
RETRY_INTERVAL_SECONDS = 0.5


def unit_active(unit):
    deadline = time.monotonic() + UNREACHABLE_RETRY_SECONDS
    while True:
        state = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", unit],
            stderr=subprocess.DEVNULL,
        )
        if state.returncode != SYSTEMD_UNREACHABLE or time.monotonic() >= deadline:
            return state.returncode == 0
        time.sleep(RETRY_INTERVAL_SECONDS)
