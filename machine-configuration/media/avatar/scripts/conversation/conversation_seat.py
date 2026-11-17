import enum
import http.client
import time

import discord_call
import listener_session
import source_capture

REMOTE_SEAT_SERVICE = "avatar-remote-seat.service"
REMOTE_SEAT_ADDRESS = ("127.0.0.1", 8769)
REMOTE_SEAT_WAIT_SECONDS = 15
POLL_SECONDS = 0.25


class Seat(enum.StrEnum):
    ROOM = "room"
    REMOTE = "remote"
    DISCORD = "discord"


MICROPHONE_BY_SEAT = {
    Seat.ROOM: "AvatarRoomMicrophone",
    Seat.REMOTE: "AvatarRemoteMicrophone.monitor",
    Seat.DISCORD: source_capture.DISCORD_DEVICE,
}
MEETING_SEATS = (Seat.ROOM, Seat.REMOTE)
MEETING_SEAT_OPTIONS = {"choices": MEETING_SEATS, "type": Seat, "default": Seat.ROOM}
REMOTE_MEETING_SOURCE = "AvatarRemoteMeeting.monitor"
SPEECH_OUTPUT_BY_SEAT = {
    Seat.ROOM: "speakers",
    Seat.REMOTE: "remote",
    Seat.DISCORD: "discord",
}


def configured(directory):
    return Seat(listener_session.read_configuration(directory).get("seat", Seat.ROOM))


def current(directory):
    if listener_session.live_purpose(directory) is None:
        return Seat.ROOM
    return configured(directory)


def requested(arguments):
    return Seat(arguments.seat or Seat.ROOM)


def remote_seat_listening():
    connection = http.client.HTTPConnection(*REMOTE_SEAT_ADDRESS, timeout=1)
    try:
        connection.request("GET", "/health")
        return connection.getresponse().status == http.HTTPStatus.OK
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def prepare_remote_seat():
    listener_session.systemctl("start", REMOTE_SEAT_SERVICE)
    deadline = time.monotonic() + REMOTE_SEAT_WAIT_SECONDS
    while not remote_seat_listening():
        if time.monotonic() > deadline:
            raise TimeoutError("The remote seat did not start listening")
        time.sleep(POLL_SECONDS)


def prepare(seat):
    if seat is Seat.DISCORD:
        discord_call.join()
    elif seat is Seat.REMOTE:
        prepare_remote_seat()
