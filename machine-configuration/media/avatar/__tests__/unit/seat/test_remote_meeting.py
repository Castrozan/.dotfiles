import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import meeting_camera
import pytest
import remote_meeting


@pytest.fixture
def mac(monkeypatch):
    mac = Mock()
    mac.ssh.return_value = SimpleNamespace(returncode=0)
    mac.attached.return_value = False
    monkeypatch.setattr(remote_meeting.subprocess, "run", mac.ssh)
    monkeypatch.setattr(local_seat, "take", mac.take)
    monkeypatch.setattr(local_seat, "leave", mac.leave)
    monkeypatch.setattr(local_seat, "attached", mac.attached)
    monkeypatch.setattr(meeting_camera, "start", mac.camera_start)
    monkeypatch.setattr(meeting_camera, "stop", mac.camera_stop)
    return mac


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(remote_meeting.sys, "argv", ["avatar-meeting", *arguments])
    with pytest.raises(SystemExit) as finished:
        remote_meeting.main()
    return finished.value.code


def ssh_commands(mac):
    return [call.args[0] for call in mac.ssh.call_args_list]


def test_starting_seats_the_meeting_page_then_opens_the_camera_then_names_the_devices(
    mac, monkeypatch, capsys
):
    assert run_main(monkeypatch, "start") == 0
    assert [call[0] for call in mac.mock_calls] == ["ssh", "take", "camera_start"]
    assert ssh_commands(mac) == [["ssh", "chise", "avatar-start --seat remote"]]
    mac.take.assert_called_once_with("?meeting")
    ready = capsys.readouterr().out
    assert ready.count("\n") == 1
    for device in ("OBS Virtual Camera", "BlackHole 2ch", "BlackHole 16ch"):
        assert device in ready


def test_every_ssh_call_has_a_timeout(mac, monkeypatch):
    run_main(monkeypatch, "start")
    run_main(monkeypatch, "stop")
    run_main(monkeypatch, "listen", "read")
    assert all(call.kwargs["timeout"] for call in mac.ssh.call_args_list)


def test_a_failed_avatar_start_ends_with_its_reason_and_undoes_nothing(
    mac, monkeypatch, capsys
):
    mac.ssh.return_value = SimpleNamespace(returncode=3)
    assert run_main(monkeypatch, "start") == 1
    assert [call[0] for call in mac.mock_calls] == ["ssh"]
    assert "avatar-start failed on chise with exit code 3" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("failing_step", "failure"),
    [
        ("take", TimeoutError("The seat page did not attach")),
        ("camera_start", RuntimeError("OBS Studio is not installed")),
    ],
)
def test_a_failure_after_the_remote_start_undoes_every_earlier_step(
    mac, monkeypatch, capsys, failing_step, failure
):
    getattr(mac, failing_step).side_effect = failure
    assert run_main(monkeypatch, "start") == 1
    steps = [call[0] for call in mac.mock_calls]
    assert steps[-3:] == ["camera_stop", "leave", "ssh"]
    assert ssh_commands(mac)[-1] == ["ssh", "chise", "avatar-stop"]
    reported = capsys.readouterr()
    assert str(failure) in reported.err
    assert "BlackHole 2ch" not in reported.out


def test_an_undo_that_cannot_reach_the_avatar_does_not_hide_the_first_failure(
    mac, monkeypatch, capsys
):
    mac.camera_start.side_effect = RuntimeError("OBS Studio is not installed")
    mac.ssh.side_effect = [
        SimpleNamespace(returncode=0),
        subprocess.TimeoutExpired("ssh", 1),
    ]
    assert run_main(monkeypatch, "start") == 1
    assert "OBS Studio is not installed" in capsys.readouterr().err


def test_stopping_closes_the_camera_and_the_seat_before_stopping_the_avatar(
    mac, monkeypatch
):
    assert run_main(monkeypatch, "stop") == 0
    assert [call[0] for call in mac.mock_calls] == ["camera_stop", "leave", "ssh"]
    assert ssh_commands(mac) == [["ssh", "chise", "avatar-stop"]]


@pytest.mark.parametrize("returncode", [0, 1, 255])
def test_stopping_exits_with_the_code_of_the_ssh(mac, monkeypatch, returncode):
    mac.ssh.return_value = SimpleNamespace(returncode=returncode)
    assert run_main(monkeypatch, "stop") == returncode


def test_listening_forwards_every_argument_quoted_like_the_talk_forwarder(
    mac, monkeypatch
):
    run_main(monkeypatch, "listen", "read", "--since", "3", "--language", "pt BR")
    assert ssh_commands(mac) == [
        ["ssh", "chise", "avatar-listen read --since 3 --language 'pt BR'"]
    ]
    mac.attached.assert_not_called()


def test_listening_exits_with_the_code_of_the_ssh(mac, monkeypatch):
    mac.ssh.return_value = SimpleNamespace(returncode=7)
    assert run_main(monkeypatch, "listen", "stop") == 7


def test_a_start_from_a_mac_holding_the_seat_listens_at_the_remote_seat(
    mac, monkeypatch
):
    mac.attached.return_value = True
    run_main(monkeypatch, "listen", "start", "--language", "pt")
    assert ssh_commands(mac) == [
        ["ssh", "chise", "avatar-listen start --language pt --seat remote"]
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["start", "--seat", "room"],
        ["start", "--seat=room"],
        ["start", "--language", "pt", "--seat", "remote"],
    ],
)
def test_a_seat_that_was_given_is_never_overridden(mac, monkeypatch, arguments):
    mac.attached.return_value = True
    run_main(monkeypatch, "listen", *arguments)
    assert ssh_commands(mac) == [
        ["ssh", "chise", "avatar-listen " + " ".join(arguments)]
    ]


def test_a_start_from_a_mac_without_the_seat_listens_in_the_room(mac, monkeypatch):
    run_main(monkeypatch, "listen", "start")
    assert ssh_commands(mac) == [["ssh", "chise", "avatar-listen start"]]


@pytest.mark.parametrize("verb", ["read", "follow", "stop", "status", "voices"])
def test_only_a_start_is_given_a_seat(mac, monkeypatch, verb):
    mac.attached.return_value = True
    run_main(monkeypatch, "listen", verb)
    assert ssh_commands(mac) == [["ssh", "chise", f"avatar-listen {verb}"]]


@pytest.mark.parametrize("arguments", [[], ["fly"], ["start", "now"], ["stop", "now"]])
def test_anything_else_is_a_usage_error(mac, monkeypatch, capsys, arguments):
    assert run_main(monkeypatch, *arguments) == 1
    assert "Usage: avatar-start | avatar-stop" in capsys.readouterr().err
    mac.ssh.assert_not_called()


def test_the_meeting_page_reuses_the_seat_machinery_with_its_query(monkeypatch):
    opened = Mock()
    monkeypatch.setattr(local_seat.subprocess, "run", opened)
    local_seat.open_browser("?meeting")
    command = opened.call_args.args[0]
    assert "--app=http://localhost:8769/?meeting" in command
    assert "--headless=new" in command
    local_seat.open_browser()
    assert "--app=http://localhost:8769/" in opened.call_args.args[0]


def test_taking_the_seat_opens_the_page_with_the_query_it_was_given(monkeypatch):
    for step in ("leave", "wait_for_tunnel", "wait_until_attached"):
        monkeypatch.setattr(local_seat, step, Mock())
    monkeypatch.setattr(local_seat.subprocess, "Popen", Mock())
    open_browser = Mock()
    monkeypatch.setattr(local_seat, "open_browser", open_browser)
    local_seat.take("?meeting")
    open_browser.assert_called_once_with("?meeting")
