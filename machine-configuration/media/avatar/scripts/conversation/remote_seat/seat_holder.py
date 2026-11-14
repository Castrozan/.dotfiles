import pathlib
import signal
import subprocess
import sys
import time

import local_seat
import meeting_camera

ROUND_SECONDS = 10
LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED = 3
SEAT_LOG = pathlib.Path(".local/share/avatar/seat-holder.log")
CAMERA_FAILURES = (RuntimeError, OSError, subprocess.SubprocessError)


class NoCamera:
    def started(self):
        return False

    def running(self):
        return False

    def stop(self):
        return None


class CameraKeeper:
    def __init__(self, camera):
        self.camera = camera
        self.owed = False
        self.looks_without_a_meeting = 0

    def look(self, seat):
        if seat is None:
            return
        if not seat.get("meeting"):
            self.miss_the_meeting()
            return
        self.looks_without_a_meeting = 0
        self.keep_the_camera()

    def keep_the_camera(self):
        self.owed = self.owed or self.camera.started()
        if self.owed and not self.camera.running():
            self.revive()

    def miss_the_meeting(self):
        self.looks_without_a_meeting += 1
        if self.looks_without_a_meeting == LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED:
            self.end()

    def end(self):
        self.owed = False
        self.camera.stop()

    def revive(self):
        try:
            self.camera.start()
        except CAMERA_FAILURES as error:
            print(error, file=sys.stderr, flush=True)


def report_to_the_seat_log():
    log = pathlib.Path.home() / SEAT_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    sys.stderr = log.open("w")


def camera_of_a_seat_opened_as(query):
    if query == local_seat.MEETING_PAGE_QUERY:
        return meeting_camera
    return NoCamera()


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
        keeper.end()
        local_seat.close_browsers()


def end_on_request(signal_number, frame):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, end_on_request)
    report_to_the_seat_log()
    hold_seat(CameraKeeper(camera_of_a_seat_opened_as("".join(sys.argv[1:]))))
