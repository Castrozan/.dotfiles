import signal
import subprocess
from unittest.mock import Mock

import local_seat
import pytest
import seat_holder

MEETING = {"meeting": True}


class Tunnel:
    def __init__(self, rounds_open):
        self.rounds_open = rounds_open
        self.terminated = False

    def wait(self, timeout):
        assert timeout == seat_holder.ROUND_SECONDS
        if self.rounds_open == 0:
            return 0
        self.rounds_open -= 1
        raise subprocess.TimeoutExpired("ssh", timeout)

    def poll(self):
        return None if self.rounds_open else 0

    def terminate(self):
        self.terminated = True


@pytest.fixture
def seat(monkeypatch):
    seat = Mock()
    seat.health.return_value = MEETING
    monkeypatch.setattr(local_seat, "health", seat.health)
    monkeypatch.setattr(local_seat, "close_browsers", seat.close_browsers)
    monkeypatch.setattr(seat_holder.signal, "signal", seat.signal)
    seat.open_tunnel = lambda rounds_open: monkeypatch.setattr(
        seat_holder.subprocess, "Popen", lambda command, **options: Tunnel(rounds_open)
    )
    return seat


def test_the_holder_looks_once_per_round_while_the_tunnel_stays_open(seat):
    seat.open_tunnel(3)
    keeper = Mock()
    seat_holder.hold_seat(keeper)
    assert keeper.look.call_count == 3
    keeper.look.assert_called_with(MEETING)


def test_a_tunnel_that_ends_stops_the_camera_then_closes_the_browsers(seat):
    seat.open_tunnel(1)
    camera = Mock()
    seat_holder.hold_seat(seat_holder.MeetingSeat(camera))
    camera.stop.assert_called_once_with()
    seat.close_browsers.assert_called_once_with()


def test_a_seat_that_ends_before_its_first_look_still_stops_the_camera(seat):
    seat.open_tunnel(0)
    camera = Mock()
    seat_holder.hold_seat(seat_holder.MeetingSeat(camera))
    camera.stop.assert_called_once_with()


def test_a_holder_asked_to_end_still_stops_the_camera_and_the_browsers(seat):
    seat.open_tunnel(5)
    camera = Mock()
    keeper = seat_holder.MeetingSeat(camera)
    seat.health.side_effect = lambda: seat_holder.end_on_request(15, None)
    with pytest.raises(SystemExit):
        seat_holder.hold_seat(keeper)
    camera.stop.assert_called_once_with()
    seat.close_browsers.assert_called_once_with()
    seat.signal.assert_called_once_with(signal.SIGTERM, signal.SIG_IGN)


def test_a_camera_that_cannot_be_stopped_still_lets_the_browsers_close(seat):
    seat.open_tunnel(0)
    camera = Mock()
    camera.stop.side_effect = OSError("pkill is missing")
    seat_holder.hold_seat(seat_holder.MeetingSeat(camera))
    seat.close_browsers.assert_called_once_with()


def test_a_meeting_that_ended_on_the_host_ends_the_holder_and_its_camera(seat):
    seat.open_tunnel(20)
    seat.health.return_value = {"meeting": False}
    camera = Mock()
    seat_holder.hold_seat(seat_holder.MeetingSeat(camera))
    assert seat.health.call_count == seat_holder.LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED
    camera.stop.assert_called_once_with()
    seat.close_browsers.assert_called_once_with()


def test_the_holder_never_outlives_the_longest_seat(seat, monkeypatch):
    seat.open_tunnel(5)
    clock = iter([0, 0, local_seat.LONGEST_SEAT_SECONDS + 1])
    monkeypatch.setattr(seat_holder.time, "monotonic", lambda: next(clock))
    keeper = Mock()
    seat_holder.hold_seat(keeper)
    assert keeper.look.call_count == 1


def test_the_seat_starts_this_holder():
    assert local_seat.HOLDER_PATH.samefile(seat_holder.__file__)
