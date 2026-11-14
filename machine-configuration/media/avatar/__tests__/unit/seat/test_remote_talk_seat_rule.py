import json
import subprocess
import sys
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


def closing(monkeypatch, health):
    order = Mock()
    order.run.return_value = SimpleNamespace(returncode=0)
    monkeypatch.setattr(remote_talk.subprocess, "run", order.run)
    monkeypatch.setattr(local_seat, "leave", order.leave)
    monkeypatch.setattr(local_seat, "health", lambda: health)
    assert run_main(monkeypatch, "close") == 0
    return [call[0] for call in order.mock_calls]


def test_closing_a_conversation_keeps_the_seat_a_meeting_still_holds(monkeypatch):
    held = {"attached": True, "listening": False, "meeting": True}
    assert closing(monkeypatch, held) == ["run"]


def test_closing_a_conversation_with_no_meeting_leaves_the_seat(monkeypatch):
    free = {"attached": True, "listening": False, "meeting": False}
    assert closing(monkeypatch, free) == ["run", "leave"]


def test_a_meeting_seat_kept_here_is_neither_retaken_nor_left_by_a_conversation(
    monkeypatch,
):
    monkeypatch.setattr(local_seat, "meeting_seat_kept_here", lambda: True)
    monkeypatch.setattr(local_seat, "health", lambda: None)
    for step in ("take", "leave"):
        monkeypatch.setattr(local_seat, step, Mock(side_effect=AssertionError(step)))
    status = '{"open": true, "seat": "remote"}'
    answer = SimpleNamespace(returncode=0, stdout=status)
    monkeypatch.setattr(remote_talk.subprocess, "run", Mock(return_value=answer))
    assert remote_talk.open_here(["open"]) == 0
    assert remote_talk.close_everywhere(["close"]) == 0


@pytest.mark.parametrize(("query", "kept"), [("?meeting", True), ("", False)])
def test_a_meeting_seat_is_found_by_the_holder_told_it_holds_a_meeting(
    monkeypatch, tmp_path, query, kept
):
    monkeypatch.undo()
    holder_script = f"{tmp_path.name}/seat_holder.py"
    monkeypatch.setattr(local_seat, "HOLDER_SCRIPT", holder_script)
    waiting = "import time; print(flush=True); time.sleep(30)"
    holder = subprocess.Popen(
        [sys.executable, "-c", waiting, f"/{holder_script}", query],
        stdout=subprocess.PIPE,
    )
    holder.stdout.readline()
    try:
        assert local_seat.meeting_seat_kept_here() == kept
    finally:
        holder.kill()
        holder.wait()
        holder.stdout.close()
