import json
import os
import socket
import sys

OSD_SOCKET_PATH = os.environ.get("XDG_RUNTIME_DIR", "/tmp") + "/quickshell-osd.sock"


def write_json_to_osd_socket(payload: dict) -> None:
    if not os.path.exists(OSD_SOCKET_PATH):
        return

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(OSD_SOCKET_PATH)
            sock.sendall((json.dumps(payload) + "\n").encode())
    except (ConnectionRefusedError, OSError):
        pass


def send_osd_value_message(osd_type: str, value: int, muted: bool = False) -> None:
    write_json_to_osd_socket({"type": osd_type, "value": value, "muted": muted})


def send_osd_mute_message(osd_type: str, muted_state: bool) -> None:
    write_json_to_osd_socket({"type": osd_type, "value": 0, "muted": muted_state})


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: quickshell-osd-send {volume|brightness|mute|mic|mic-mute} <value>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    osd_type = sys.argv[1]
    osd_value = sys.argv[2]

    match osd_type:
        case "volume":
            send_osd_value_message("volume", int(osd_value))
        case "brightness":
            send_osd_value_message("brightness", int(osd_value))
        case "mute":
            send_osd_mute_message("volume", osd_value.lower() == "true")
        case "mic":
            send_osd_value_message("mic", int(osd_value))
        case "mic-mute":
            send_osd_mute_message("mic", osd_value.lower() == "true")
        case _:
            print(
                "Usage: quickshell-osd-send"
                " {volume|brightness|mute|mic|mic-mute} <value>",
                file=sys.stderr,
            )
            raise SystemExit(1)


if __name__ == "__main__":
    main()
