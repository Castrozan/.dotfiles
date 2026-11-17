import sys

import mac_seat_client
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

OPEN_TIMEOUT_SECONDS = 5


def copy_call_audio(output):
    with connect(
        f"ws://{mac_seat_client.HOST}:{mac_seat_client.PORT}{mac_seat_client.CALL_PATH}",
        origin=mac_seat_client.ORIGIN,
        open_timeout=OPEN_TIMEOUT_SECONDS,
    ) as call:
        for frame in call:
            if isinstance(frame, bytes):
                output.write(frame)
                output.flush()


def main():
    try:
        copy_call_audio(sys.stdout.buffer)
    except (OSError, WebSocketException):
        sys.exit(1)


if __name__ == "__main__":
    main()
