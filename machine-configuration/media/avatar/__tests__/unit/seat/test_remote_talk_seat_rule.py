import json
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import pytest
import remote_talk


def chise_answers(monkeypatch, seat="remote"):
    status = json.dumps({"open": True, "live": False, "seat": seat, "last_heard": 0})
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=status))
    monkeypatch.setattr(remote_talk.subprocess, "run", runner)
    return runner


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(remote_talk.sys, "argv", ["avatar-talk", *arguments])
    with pytest.raises(SystemExit) as finished:
        remote_talk.main()
    return finished.value.code


@pytest.fixture
def seat_here(monkeypatch):
    monkeypatch.setattr(local_seat, "attached", lambda: False)
    take = Mock()
    monkeypatch.setattr(local_seat, "take", take)
    return take


@pytest.mark.parametrize("user_here", [True, False])
def test_an_explicit_remote_seat_is_taken_here_whatever_the_idle_time(
    monkeypatch, seat_here, user_here
):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: user_here)
    runner = chise_answers(monkeypatch)
    assert run_main(monkeypatch, "open", "--seat", "remote", "--language", "pt") == 0
    assert runner.call_args.args[0] == [
        "ssh",
        "chise",
        "avatar-talk",
        "open --seat remote --language pt",
    ]
    seat_here.assert_called_once_with()


@pytest.mark.parametrize("user_here", [True, False])
def test_an_explicit_room_seat_is_forwarded_unchanged(
    monkeypatch, seat_here, user_here
):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: user_here)
    runner = chise_answers(monkeypatch, seat="room")
    assert run_main(monkeypatch, "open", "--seat", "room") == 0
    assert runner.call_args.args[0] == [
        "ssh",
        "chise",
        "avatar-talk",
        "open --seat room",
    ]
    seat_here.assert_not_called()


@pytest.mark.parametrize(
    ("arguments", "user_here", "here"),
    [
        (["open"], True, True),
        (["open"], False, False),
        (["open", "--seat", "remote"], False, True),
        (["open", "--seat", "room"], True, False),
        (["open", "--live", "--seat", "remote"], False, True),
        (["ask", "--seat", "remote"], True, False),
        (["close"], True, False),
        ([], True, False),
    ],
)
def test_an_open_is_seated_here_for_the_remote_seat_or_a_user_who_is_here(
    monkeypatch, arguments, user_here, here
):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: user_here)
    assert remote_talk.opens_here(arguments) is here


def test_opening_here_does_not_repeat_a_remote_seat_already_named(monkeypatch):
    runner = chise_answers(monkeypatch)
    monkeypatch.setattr(local_seat, "attached", lambda: True)
    remote_talk.open_here(["open", "--seat", "remote"])
    assert runner.call_args.args[0][-1] == "open --seat remote"
    remote_talk.open_here(["open"])
    assert runner.call_args.args[0][-1] == "open --seat remote"
