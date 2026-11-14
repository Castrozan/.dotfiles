import subprocess
from unittest.mock import Mock

import pytest
import seat_holder
from hypothesis import given
from hypothesis import strategies as st

MEETING = {"meeting": True}
NO_MEETING = {"meeting": False}
UNREACHABLE = None


class Camera:
    def __init__(self, running=False, started=False):
        self.is_running = running
        self.has_started = started
        self.starts = 0
        self.stops = 0
        self.start_failure = None
        self.leaves_obs_running = False

    def running(self):
        return self.is_running

    def started(self):
        return self.has_started

    def start(self):
        self.starts += 1
        self.has_started = False
        if self.start_failure:
            self.is_running = self.leaves_obs_running
            raise self.start_failure
        self.is_running = self.has_started = True

    def stop(self):
        self.stops += 1
        self.is_running = self.has_started = False


def look_each(keeper, *seats):
    for seat in seats:
        keeper.look(seat)


def test_a_started_camera_that_vanished_during_a_meeting_is_started_again():
    camera = Camera(running=False, started=True)
    seat_holder.MeetingSeat(camera).look(MEETING)
    assert camera.starts == 1
    assert camera.is_running


def test_a_camera_still_being_started_is_left_to_whoever_starts_it():
    camera = Camera(running=False, started=False)
    look_each(seat_holder.MeetingSeat(camera), MEETING, MEETING)
    assert camera.starts == 0


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("OBS did not start"), subprocess.TimeoutExpired("open", 1)],
)
def test_a_failed_start_is_reported_and_tried_again_on_the_next_look(failure, capsys):
    camera = Camera(running=False, started=True)
    keeper = seat_holder.MeetingSeat(camera)
    camera.start_failure = failure
    keeper.look(MEETING)
    assert not camera.has_started
    camera.start_failure = None
    keeper.look(MEETING)
    assert camera.starts == 2
    assert camera.is_running
    assert str(failure) in capsys.readouterr().err


def test_a_meeting_gone_from_the_host_for_six_looks_ends_the_seat():
    keeper = seat_holder.MeetingSeat(Camera(running=True, started=True))
    goes_on = [keeper.look(seat) for seat in [MEETING, *[NO_MEETING] * 6]]
    assert goes_on == [True] * 6 + [False]


def test_a_meeting_that_blinks_keeps_its_seat_and_camera():
    camera = Camera(running=True, started=True)
    keeper = seat_holder.MeetingSeat(camera)
    blinks = [MEETING, *[NO_MEETING] * 5, MEETING, *[NO_MEETING] * 5]
    assert all(keeper.look(seat) for seat in blinks)
    assert camera.stops == 0
    camera.is_running = False
    keeper.look(MEETING)
    assert camera.starts == 1


def test_an_unreachable_seat_changes_nothing():
    camera = Camera(running=False, started=True)
    look_each(seat_holder.MeetingSeat(camera), *[UNREACHABLE] * 5)
    assert (camera.starts, camera.stops) == (0, 0)


def test_obs_left_running_by_a_failed_start_is_stopped_and_started_again():
    camera = Camera(running=False, started=True)
    keeper = seat_holder.MeetingSeat(camera)
    camera.start_failure = RuntimeError("OBS did not start its virtual camera")
    camera.leaves_obs_running = True
    keeper.look(MEETING)
    assert not camera.is_running
    camera.start_failure = None
    keeper.look(MEETING)
    assert (camera.starts, camera.is_running) == (2, True)


def test_a_camera_that_cannot_be_asked_is_reported_and_the_holder_goes_on(capsys):
    camera = Camera(started=True)
    camera.running = Mock(side_effect=subprocess.TimeoutExpired("pgrep", 30))
    keeper = seat_holder.MeetingSeat(camera)
    keeper.look(MEETING)
    camera.stop = Mock(side_effect=OSError("pkill is missing"))
    keeper.end()
    assert "pgrep" in capsys.readouterr().err


LOOKS = st.tuples(st.sampled_from([MEETING, NO_MEETING, UNREACHABLE]), st.booleans())


@given(st.lists(LOOKS, max_size=30), st.booleans(), st.booleans())
def test_the_seat_and_camera_follow_the_meeting_whatever_the_looks(looks, running, started):
    camera = Camera(running, started)
    keeper = seat_holder.MeetingSeat(camera)
    camera.leaves_obs_running = True
    seen_sending = False
    missed = 0
    for seat, start_fails in looks:
        camera.start_failure = RuntimeError("no camera") if start_fails else None
        seen_sending = seen_sending or (seat is MEETING and camera.has_started)
        was_running = camera.is_running
        goes_on = keeper.look(seat)
        missed = missed + 1 if seat is NO_MEETING else 0 if seat is MEETING else missed
        if seat is MEETING and seen_sending:
            assert camera.is_running == (was_running or not start_fails)
        assert goes_on == (missed < seat_holder.LOOKS_WITHOUT_A_MEETING_BEFORE_IT_ENDED)
        if not goes_on:
            return
