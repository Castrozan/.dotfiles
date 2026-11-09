import socket
import time
from pathlib import Path

from hyprland_runtime import build_event_socket_path
from monitor_configuration import reconcile_with_connected_monitors

RECONNECT_INITIAL_DELAY_SECONDS = 1
RECONNECT_MAX_DELAY_SECONDS = 30
MONITOR_CHANGE_EVENTS = frozenset({"monitoradded", "monitorremoved"})


def reconcile_and_dispatch_events(event_socket_path: str) -> None:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(event_socket_path)
        reconcile_with_connected_monitors()
        with sock.makefile("r") as stream:
            for line in stream:
                event, separator, _ = line.strip().partition(">>")
                if separator and event in MONITOR_CHANGE_EVENTS:
                    reconcile_with_connected_monitors()
    finally:
        sock.close()


def main() -> None:
    event_socket_path = build_event_socket_path()
    reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS

    while True:
        try:
            reconcile_and_dispatch_events(event_socket_path)
            reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS
        except OSError:
            pass

        while not Path(event_socket_path).is_socket():
            time.sleep(reconnect_delay_seconds)

        reconnect_delay_seconds = min(
            reconnect_delay_seconds * 2, RECONNECT_MAX_DELAY_SECONDS
        )


if __name__ == "__main__":
    main()
