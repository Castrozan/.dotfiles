import subprocess

import local_seat

WINDOW_SIZE = "640,360"


def hide():
    local_seat.end_processes_matching(local_seat.WINDOW_PROFILE_FLAG)


def show(port=local_seat.WINDOW_PORT):
    hide()
    open_window("?viewer", port)


def open_window(page, port=local_seat.WINDOW_PORT):
    subprocess.run(
        [
            "/usr/bin/open",
            "-n",
            "-a",
            local_seat.BROWSER_APPLICATION,
            "--args",
            local_seat.WINDOW_PROFILE_FLAG,
            f"--app=http://localhost:{port}/{page}",
            f"--window-size={WINDOW_SIZE}",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        check=True,
        timeout=local_seat.COMMAND_TIMEOUT_SECONDS,
    )
