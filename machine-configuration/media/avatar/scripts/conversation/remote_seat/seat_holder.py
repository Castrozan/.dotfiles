import signal
import subprocess
import sys
import time

import local_seat
import meeting_camera

ROUND_SECONDS = 10
CAMERA_FAILURES = (RuntimeError, OSError, subprocess.SubprocessError)


class CameraKeeper:
    def __init__(self, camera=meeting_camera):
        self.camera = camera
        self.meeting_seen = False
        self.camera_seen = False

    def look(self, seat):
        if seat is None:
            return
        if not seat.get("meeting"):
            self.end_with_the_meeting()
            return
        self.meeting_seen = True
        if self.camera.running():
            self.camera_seen = True
        elif self.camera_seen:
            self.revive()

    def end_with_the_meeting(self):
        if self.meeting_seen:
            self.camera.stop()
        self.meeting_seen = False
        self.camera_seen = False

    def revive(self):
        try:
            self.camera.start()
        except CAMERA_FAILURES as error:
            print(error, file=sys.stderr)


def tunnel_stays_open(tunnel):
    try:
        tunnel.wait(timeout=ROUND_SECONDS)
    except subprocess.TimeoutExpired:
        return True
    return False


def hold_seat(keeper):
    tunnel = subprocess.Popen(local_seat.TUNNEL_COMMAND)
    deadline = time.monotonic() + local_seat.LONGEST_SEAT_SECONDS
    try:
        while time.monotonic() < deadline and tunnel_stays_open(tunnel):
            keeper.look(local_seat.health())
    finally:
        tunnel.terminate()
        keeper.end_with_the_meeting()
        local_seat.close_browsers()


def end_on_request(signal_number, frame):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, end_on_request)
    hold_seat(CameraKeeper())
