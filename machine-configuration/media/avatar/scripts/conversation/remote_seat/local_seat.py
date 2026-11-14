import http.client
import json
import pathlib
import subprocess
import sys
import time

AVATAR_HOST = "chise"
SEAT_PORT = 8769
WINDOW_PORT = 8770
RENDERER_PORT = 3000
CONTROL_PORT = 8765
TUNNEL_FORWARD = f"127.0.0.1:{SEAT_PORT}:127.0.0.1:{SEAT_PORT}"
WINDOW_FORWARDS = [
    f"127.0.0.1:{WINDOW_PORT}:127.0.0.1:{RENDERER_PORT}",
    f"127.0.0.1:{CONTROL_PORT}:127.0.0.1:{CONTROL_PORT}",
]
WAIT_WHILE_SEAT_SERVES = (
    "systemctl --user is-active --quiet avatar-remote-seat.service"
    " && systemctl --user start --wait avatar-remote-seat.service"
)
TUNNEL_COMMAND = [
    "ssh",
    "-o",
    "BatchMode=yes",
    "-o",
    "ExitOnForwardFailure=yes",
    "-o",
    "ServerAliveInterval=5",
    "-o",
    "ServerAliveCountMax=3",
    *(
        option
        for forward in (TUNNEL_FORWARD, *WINDOW_FORWARDS)
        for option in ("-L", forward)
    ),
    AVATAR_HOST,
    WAIT_WHILE_SEAT_SERVES,
]
BROWSER = "Google Chrome"
BROWSER_PROFILE = pathlib.Path.home() / ".local/share/avatar/seat-browser"
BROWSER_PROFILE_FLAG = f"--user-data-dir={BROWSER_PROFILE}"
WINDOW_PROFILE = pathlib.Path.home() / ".local/share/avatar/window-browser"
WINDOW_PROFILE_FLAG = f"--user-data-dir={WINDOW_PROFILE}"
HOLDER_SCRIPT = "remote_seat/seat_holder.py"
HOLDER_PATH = pathlib.Path(__file__).with_name("seat_holder.py")
TUNNEL_WAIT_SECONDS = 15
LONGEST_SEAT_SECONDS = 12 * 60 * 60
COMMAND_TIMEOUT_SECONDS = 30
ATTACH_WAIT_SECONDS = 20
POLL_SECONDS = 0.25


def health():
    connection = http.client.HTTPConnection("127.0.0.1", SEAT_PORT, timeout=1)
    try:
        connection.request("GET", "/health")
        return json.loads(connection.getresponse().read())
    except (OSError, http.client.HTTPException, ValueError):
        return None
    finally:
        connection.close()


def attached():
    return bool((health() or {}).get("attached"))


def conversation_listening():
    return bool((health() or {}).get("listening"))


def meeting_held():
    return bool((health() or {}).get("meeting"))


def end_processes_matching(command_line, signal_name="TERM"):
    subprocess.run(
        ["/usr/bin/pkill", f"-{signal_name}", "-f", "--", command_line],
        check=False,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def close_browsers():
    for profile_flag in (BROWSER_PROFILE_FLAG, WINDOW_PROFILE_FLAG):
        end_processes_matching(profile_flag)


def leave():
    for command_line in (HOLDER_SCRIPT, TUNNEL_FORWARD):
        end_processes_matching(command_line)
    close_browsers()


def wait_for_tunnel():
    deadline = time.monotonic() + TUNNEL_WAIT_SECONDS
    while health() is None:
        if time.monotonic() > deadline:
            raise TimeoutError("The tunnel to the avatar did not open")
        time.sleep(POLL_SECONDS)


def wait_until_attached():
    deadline = time.monotonic() + ATTACH_WAIT_SECONDS
    while time.monotonic() < deadline:
        seat = health() or {}
        if seat.get("attached"):
            return
        if seat.get("failure"):
            raise RuntimeError(
                f"This machine could not take the seat: {seat['failure']}"
            )
        time.sleep(POLL_SECONDS)
    raise TimeoutError(
        f"The seat page did not attach; check that {BROWSER} may use the microphone"
    )


def open_headless_browser(profile_flag, port, *extra_flags, query=""):
    subprocess.run(
        [
            "/usr/bin/open",
            "-g",
            "-n",
            "-a",
            BROWSER,
            "--args",
            "--headless=new",
            profile_flag,
            f"--app=http://localhost:{port}/{query}",
            "--use-fake-ui-for-media-stream",
            *extra_flags,
            "--no-first-run",
            "--no-default-browser-check",
        ],
        check=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def open_browser(query=""):
    open_headless_browser(
        BROWSER_PROFILE_FLAG,
        SEAT_PORT,
        "--autoplay-policy=no-user-gesture-required",
        query=query,
    )


def take(query=""):
    leave()
    try:
        subprocess.Popen(
            [sys.executable, str(HOLDER_PATH)],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for_tunnel()
        open_browser(query)
        wait_until_attached()
    except BaseException:
        leave()
        raise

