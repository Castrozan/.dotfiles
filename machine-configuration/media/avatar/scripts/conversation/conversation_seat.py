import enum
import http.client
import time

import listener_session

REMOTE_SEAT_SERVICE = "avatar-remote-seat.service"
REMOTE_SEAT_ADDRESS = ("127.0.0.1", 8769)
REMOTE_SEAT_WAIT_SECONDS = 15
POLL_SECONDS = 0.25


class Seat(enum.StrEnum):
    ROOM = "room"
    REMOTE = "remote"


MICROPHONE_BY_SEAT = {
    Seat.ROOM: "AvatarRoomMicrophone",
    Seat.REMOTE: "AvatarRemoteMicrophone.monitor",
}
REMOTE_MEETING_SOURCE = "AvatarRemoteMeeting.monitor"
SPEECH_OUTPUT_BY_SEAT = {Seat.ROOM: "speakers", Seat.REMOTE: "remote"}


def configured(directory):
    return Seat(listener_session.read_configuration(directory).get("seat", Seat.ROOM))


def current(directory):
    if listener_session.live_purpose(directory) is None:
        return Seat.ROOM
    return configured(directory)


def remote_seat_listening():
    connection = http.client.HTTPConnection(*REMOTE_SEAT_ADDRESS, timeout=1)
    try:
        connection.request("GET", "/health")
        return connection.getresponse().status == http.HTTPStatus.OK
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def prepare(seat):
    if seat is not Seat.REMOTE:
        return
    listener_session.systemctl("start", REMOTE_SEAT_SERVICE)
    deadline = time.monotonic() + REMOTE_SEAT_WAIT_SECONDS
    while not remote_seat_listening():
        if time.monotonic() > deadline:
            raise TimeoutError("The remote seat did not start listening")
        time.sleep(POLL_SECONDS)
