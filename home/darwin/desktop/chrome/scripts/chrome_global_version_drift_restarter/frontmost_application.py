from __future__ import annotations

import subprocess

LIST_APPLICATION_INFORMATION_BINARY_PATH = "/usr/bin/lsappinfo"
CHROME_FRONTMOST_DISPLAY_NAME = "Google Chrome"
SUBPROCESS_QUERY_TIMEOUT_SECONDS = 15.0


def frontmost_name_report_indicates_chrome(frontmost_name_report: str) -> bool:
    return f'"LSDisplayName"="{CHROME_FRONTMOST_DISPLAY_NAME}"' in frontmost_name_report


def read_frontmost_application_name_report() -> str:
    try:
        frontmost_application_serial_number = subprocess.run(
            [LIST_APPLICATION_INFORMATION_BINARY_PATH, "front"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_QUERY_TIMEOUT_SECONDS,
            check=False,
        ).stdout.strip()
        if not frontmost_application_serial_number:
            return ""
        return subprocess.run(
            [
                LIST_APPLICATION_INFORMATION_BINARY_PATH,
                "info",
                "-only",
                "name",
                frontmost_application_serial_number,
            ],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_QUERY_TIMEOUT_SECONDS,
            check=False,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def chrome_is_the_frontmost_application() -> bool:
    return frontmost_name_report_indicates_chrome(
        read_frontmost_application_name_report()
    )
