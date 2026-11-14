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


def test_what_the_holder_reports_joins_the_seat_log_with_its_time(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(seat_holder.sys, "stderr", None)
    log = tmp_path / ".local/share/avatar/seat-holder.log"
    log.parent.mkdir(parents=True)
    log.write_text("an earlier seat\n")
    seat_holder.report_to_the_seat_log()
    seat_holder.MeetingSeat(FailingCamera()).look({"meeting": True})
    seat_holder.sys.stderr.close()
    earlier, failure = log.read_text().splitlines()
    assert earlier == "an earlier seat"
    assert failure.endswith(" OBS Studio is not installed")
    assert failure[:4].isdigit()


@pytest.mark.parametrize(
    ("arguments", "camera"),
    [([], "ConversationSeat"), ([local_seat.MEETING_PAGE_QUERY], "MeetingSeat")],
)
def test_the_holder_keeps_the_seat_its_arguments_name(monkeypatch, arguments, camera):
    held = Mock()
    monkeypatch.setattr(seat_holder, "hold_seat", held)
    monkeypatch.setattr(seat_holder, "report_to_the_seat_log", Mock())
    monkeypatch.setattr(seat_holder.signal, "signal", Mock())
    seat_holder.main(arguments)
    assert type(held.call_args.args[0]).__name__ == camera


def test_a_seat_log_that_cannot_be_opened_leaves_the_holder_reporting_as_before(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / ".local").write_text("not a directory")
    monkeypatch.setenv("HOME", str(tmp_path))
    seat_holder.report_to_the_seat_log()
    assert "Not a directory" in capsys.readouterr().err


class FailingCamera:
    def started(self):
        return True

    def running(self):
        return False

    def start(self):
        raise RuntimeError("OBS Studio is not installed")

    def stop(self):
        return None


MEETING = {"meeting": True}
NO_MEETING = {"meeting": False}


def test_a_seat_opened_for_a_conversation_keeps_no_camera_and_outlives_meetings(
    monkeypatch,
):
    for step in ("start", "stop", "running", "started"):
        monkeypatch.setattr(
            seat_holder.meeting_camera, step, Mock(side_effect=AssertionError)
        )
    keeper = seat_holder.seat_opened_as("")
    assert all(keeper.look(seat) for seat in [MEETING, *[NO_MEETING] * 10, None])
    keeper.end()


def test_a_seat_opened_for_a_meeting_keeps_the_call_camera():
    keeper = seat_holder.seat_opened_as(local_seat.MEETING_PAGE_QUERY)
    assert keeper.camera is seat_holder.meeting_camera
