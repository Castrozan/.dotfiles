from __future__ import annotations

import socket
import sys

SHOW_PICKER_COMMAND = b"show"


def send_show_picker_command(daemon_socket_path: str) -> int:
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        client_socket.sendto(SHOW_PICKER_COMMAND, daemon_socket_path)
    except OSError as exception:
        print(f"application-launcher: {exception}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(send_show_picker_command(sys.argv[1]))
