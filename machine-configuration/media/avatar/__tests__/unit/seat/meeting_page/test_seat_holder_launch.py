from unittest.mock import Mock

import local_seat
import pytest
import seat_holder


@pytest.fixture
def holder(monkeypatch):
    for step in ("leave", "wait_for_tunnel", "open_browser", "wait_until_attached"):
        monkeypatch.setattr(local_seat, step, Mock())
    spawn = Mock()
    monkeypatch.setattr(local_seat.subprocess, "Popen", spawn)
    return spawn


@pytest.mark.parametrize("query", ["", local_seat.MEETING_PAGE_QUERY])
def test_the_holder_is_told_how_its_seat_was_opened(holder, query):
    local_seat.take(query)
    assert holder.call_args.args[0][1:] == [str(local_seat.HOLDER_PATH), query]


def test_what_the_holder_reports_is_kept_for_this_seat_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(seat_holder.sys, "stderr", None)
    log = tmp_path / ".local/share/avatar/seat-holder.log"
    log.parent.mkdir(parents=True)
    log.write_text("an earlier seat")
    seat_holder.report_to_the_seat_log()
    seat_holder.CameraKeeper(FailingCamera()).look({"meeting": True})
    seat_holder.sys.stderr.close()
    assert log.read_text() == "OBS Studio is not installed\n"


class FailingCamera:
    def started(self):
        return True

    def running(self):
        return False

    def start(self):
        raise RuntimeError("OBS Studio is not installed")


def look_each(keeper, *seats):
    for seat in seats:
        keeper.look(seat)


MEETING = {"meeting": True}
NO_MEETING = {"meeting": False}


def test_a_seat_opened_for_a_conversation_keeps_no_camera(monkeypatch):
    for step in ("start", "stop", "running", "started"):
        monkeypatch.setattr(
            seat_holder.meeting_camera, step, Mock(side_effect=AssertionError)
        )
    keeper = seat_holder.CameraKeeper(seat_holder.camera_of_a_seat_opened_as(""))
    look_each(keeper, MEETING, MEETING, *[NO_MEETING] * 4)
    keeper.end()


def test_a_seat_opened_for_a_meeting_keeps_the_call_camera():
    camera = seat_holder.camera_of_a_seat_opened_as(local_seat.MEETING_PAGE_QUERY)
    assert camera is seat_holder.meeting_camera
