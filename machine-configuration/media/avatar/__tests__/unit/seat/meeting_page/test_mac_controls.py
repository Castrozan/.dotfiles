import pathlib
from unittest.mock import Mock

import local_seat
import local_window
import meeting_camera
import pytest
import remote_meeting


def run_controls(monkeypatch, attached, camera_running=True):
    opened = Mock()
    ended = Mock()
    monkeypatch.setattr(local_seat, "attached", lambda: attached)
    monkeypatch.setattr(meeting_camera, "running", lambda: camera_running)
    monkeypatch.setattr(local_seat, "end_processes_matching", ended)
    monkeypatch.setattr(local_window.subprocess, "run", opened)
    monkeypatch.setattr(remote_meeting.sys, "argv", ["avatar-meeting", "controls"])
    with pytest.raises(SystemExit) as finished:
        remote_meeting.main()
    return finished.value.code, opened, ended


def test_the_controls_open_in_a_window_served_through_the_seat_tunnel(monkeypatch):
    code, opened, ended = run_controls(monkeypatch, attached=True)
    assert code == 0
    command = opened.call_args.args[0]
    assert "--app=http://localhost:8770/controls.html" in command
    assert local_seat.WINDOW_PROFILE_FLAG in command
    assert "--headless=new" not in command
    assert opened.call_args.kwargs["timeout"]


def test_opening_the_controls_keeps_an_open_avatar_window(monkeypatch):
    code, opened, ended = run_controls(monkeypatch, attached=True)
    ended.assert_not_called()


@pytest.mark.parametrize(
    ("attached", "camera_running"), [(False, True), (True, False), (False, False)]
)
def test_the_controls_refuse_unless_this_mac_shows_the_call_picture(
    monkeypatch, capsys, attached, camera_running
):
    code, opened, ended = run_controls(monkeypatch, attached, camera_running)
    assert code == 1
    opened.assert_not_called()
    assert "Run avatar-start on this Mac" in capsys.readouterr().err


def test_the_camera_choice_answers_do_not_end_another_agents_command():
    command_client = (
        pathlib.Path(remote_meeting.__file__).resolve().parents[2] / "command.js"
    ).read_text()
    identified = command_client.split("IDENTIFIED_RESPONSES = [")[1].split("]")[0]
    assert '"cameraList"' in identified
    assert '"cameraResult"' in identified
