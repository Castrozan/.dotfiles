import pathlib
import signal
import subprocess
import sys
import time

import local_seat
import meeting_camera

ROUND_SECONDS = 10
LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED = 6
SEAT_LOG = pathlib.Path(".local/share/avatar/seat-holder.log")
LONGEST_SEAT_LOG_BYTES = 1_000_000
CAMERA_FAILURES = (RuntimeError, OSError, ValueError, subprocess.SubprocessError)


class ConversationSeat:
    def look(self, seat):
        return True

    def end(self):
        return None


class MeetingSeat:
    def __init__(self, camera):
        self.camera = camera
        self.owed = False
        self.looks_without_a_meeting = 0

    def look(self, seat):
        if seat is None:
            return True
        if not seat.get("meeting"):
            self.looks_without_a_meeting += 1
            return (
                self.looks_without_a_meeting < LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED
            )
        self.looks_without_a_meeting = 0
        without_failing(self.keep_the_camera)
        return True

    def keep_the_camera(self):
        self.owed = self.owed or self.camera.started()
        if self.owed and not self.camera.running():
            self.revive()

    def end(self):
        self.owed = False
        without_failing(self.camera.stop)

    def revive(self):
        try:
            self.camera.start()
        except CAMERA_FAILURES:
            without_failing(self.camera.stop)
            raise


def without_failing(step):
    try:
        step()
    except CAMERA_FAILURES as error:
        report(error)


def report(message):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), message, file=sys.stderr, flush=True)


def report_to_the_seat_log():
    log = pathlib.Path.home() / SEAT_LOG
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        too_long = log.exists() and log.stat().st_size > LONGEST_SEAT_LOG_BYTES
        sys.stderr = log.open("w" if too_long else "a")
    except OSError as error:
        report(error)


def seat_opened_as(query):
    if query == local_seat.MEETING_PAGE_QUERY:
        return MeetingSeat(meeting_camera)
    return ConversationSeat()


def tunnel_stays_open(tunnel):
    try:
        tunnel.wait(timeout=ROUND_SECONDS)
    except subprocess.TimeoutExpired:
        return True
    return False


def hold_seat(keeper):
    tunnel = subprocess.Popen(local_seat.TUNNEL_COMMAND, stderr=sys.stderr)
    deadline = time.monotonic() + local_seat.LONGEST_SEAT_SECONDS
    try:
        while time.monotonic() < deadline and tunnel_stays_open(tunnel):
            if not keeper.look(local_seat.health()):
                report("The meeting ended on the host, so this seat ends too")
                break
    finally:
        tunnel.terminate()
        keeper.end()
        local_seat.close_browsers()


def end_on_request(signal_number, frame):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    sys.exit(0)


def main(arguments):
    signal.signal(signal.SIGTERM, end_on_request)
    report_to_the_seat_log()
    hold_seat(seat_opened_as("".join(arguments)))


if __name__ == "__main__":
    main(sys.argv[1:])
