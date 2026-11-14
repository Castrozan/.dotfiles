import subprocess
from unittest.mock import Mock

import local_seat
import pytest
import seat_holder
from hypothesis import given
from hypothesis import strategies as st

MEETING = {"meeting": True}
NO_MEETING = {"meeting": False}
UNREACHABLE = None


class Camera:
    def __init__(self, running=False):
        self.is_running = running
        self.starts = 0
        self.stops = 0
        self.start_failure = None

    def running(self):
        return self.is_running

    def start(self):
        self.starts += 1
        if self.start_failure:
            raise self.start_failure
        self.is_running = True

    def stop(self):
        self.stops += 1
        self.is_running = False


def test_a_camera_that_vanished_during_a_meeting_is_started_again():
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    camera.is_running = False
    keeper.look(MEETING)
    assert camera.starts == 1
    assert camera.is_running


def test_a_camera_this_seat_never_saw_running_is_not_started():
    camera = Camera()
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    keeper.look(MEETING)
    assert camera.starts == 0


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("OBS did not start"), subprocess.TimeoutExpired("open", 1)],
)
def test_a_failed_start_is_reported_and_tried_again_on_the_next_look(failure, capsys):
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    camera.is_running = False
    camera.start_failure = failure
    keeper.look(MEETING)
    camera.start_failure = None
    keeper.look(MEETING)
    assert camera.starts == 2
    assert camera.is_running
    assert str(failure) in capsys.readouterr().err


def test_a_meeting_that_ends_on_the_host_stops_the_camera_once():
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    keeper.look(NO_MEETING)
    keeper.look(NO_MEETING)
    assert camera.stops == 1
    assert not camera.is_running


def test_a_seat_that_never_held_a_meeting_leaves_every_camera_alone():
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(NO_MEETING)
    keeper.end_with_the_meeting()
    assert camera.stops == 0


def test_an_unreachable_seat_changes_nothing():
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    camera.is_running = False
    keeper.look(UNREACHABLE)
    assert (camera.starts, camera.stops) == (0, 0)


@given(st.lists(st.sampled_from([MEETING, NO_MEETING, UNREACHABLE]), max_size=30))
def test_the_camera_never_runs_after_a_look_that_saw_no_meeting(looks):
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    meeting_seen = False
    for seat in looks:
        keeper.look(seat)
        meeting_seen = meeting_seen or seat is MEETING
        if seat is NO_MEETING and meeting_seen:
            assert not camera.is_running
            meeting_seen = False


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

    def terminate(self):
        self.terminated = True


@pytest.fixture
def seat(monkeypatch):
    seat = Mock()
    seat.health.return_value = MEETING
    monkeypatch.setattr(local_seat, "health", seat.health)
    monkeypatch.setattr(local_seat, "close_browsers", seat.close_browsers)
    seat.open_tunnel = lambda rounds_open: monkeypatch.setattr(
        seat_holder.subprocess, "Popen", lambda command: Tunnel(rounds_open)
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
    camera = Camera(running=True)
    seat_holder.hold_seat(seat_holder.CameraKeeper(camera))
    assert camera.stops == 1
    seat.close_browsers.assert_called_once_with()


def test_a_holder_asked_to_end_still_stops_the_camera_and_the_browsers(seat):
    seat.open_tunnel(5)
    camera = Camera(running=True)
    keeper = seat_holder.CameraKeeper(camera)
    keeper.look(MEETING)
    seat.health.side_effect = lambda: seat_holder.end_on_request(15, None)
    with pytest.raises(SystemExit):
        seat_holder.hold_seat(keeper)
    assert camera.stops == 1
    seat.close_browsers.assert_called_once_with()


def test_the_holder_never_outlives_the_longest_seat(seat, monkeypatch):
    seat.open_tunnel(5)
    clock = iter([0, 0, local_seat.LONGEST_SEAT_SECONDS + 1])
    monkeypatch.setattr(seat_holder.time, "monotonic", lambda: next(clock))
    keeper = Mock()
    seat_holder.hold_seat(keeper)
    assert keeper.look.call_count == 1
