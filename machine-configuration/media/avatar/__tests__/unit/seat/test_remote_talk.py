import itertools
import json
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import pytest
import remote_talk


def chise_answers(monkeypatch, returncode=0, seat="remote"):
    status = json.dumps({"open": True, "live": False, "seat": seat, "last_heard": 0})
    runner = Mock(return_value=SimpleNamespace(returncode=returncode, stdout=status))
    monkeypatch.setattr(remote_talk.subprocess, "run", runner)
    return runner


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(remote_talk.sys, "argv", ["avatar-talk", *arguments])
    with pytest.raises(SystemExit) as finished:
        remote_talk.main()
    return finished.value.code


def forwarding(monkeypatch, returncode=0):
    forwarded = Mock(return_value=SimpleNamespace(returncode=returncode))
    monkeypatch.setattr(remote_talk.subprocess, "run", forwarded)
    return forwarded


@pytest.mark.parametrize(
    ("verb", "live", "seat"),
    itertools.product(
        ["open", "close", "ask", "say", "hear", "follow", "status", "show", "hide"],
        [False, True],
        [False, True],
    ),
)
def test_only_an_open_without_a_seat_asks_for_one_here(verb, live, seat):
    arguments = [
        verb,
        *(["--live"] if live else []),
        *(["--seat", "room"] if seat else []),
    ]
    assert remote_talk.opens_a_seated_conversation(arguments) is (
        verb == "open" and not seat
    )


def test_no_verb_at_all_is_forwarded_untouched(monkeypatch):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: True)
    forwarded = forwarding(monkeypatch, returncode=2)
    assert run_main(monkeypatch) == 2
    assert forwarded.call_args.args == (["ssh", "chise", "avatar-talk", ""],)


def test_an_open_while_the_user_is_away_stays_in_the_room(monkeypatch):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: False)
    take = Mock()
    monkeypatch.setattr(local_seat, "take", take)
    forwarded = forwarding(monkeypatch)
    assert run_main(monkeypatch, "open", "--character", "vita") == 0
    assert forwarded.call_args.args == (
        ["ssh", "chise", "avatar-talk", "open --character vita"],
    )
    assert forwarded.call_args.kwargs["timeout"] > 0
    take.assert_not_called()


def test_an_open_while_the_user_is_here_takes_the_seat(monkeypatch, capsys):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: True)
    runner = chise_answers(monkeypatch)
    monkeypatch.setattr(local_seat, "attached", lambda: False)
    take = Mock()
    monkeypatch.setattr(local_seat, "take", take)
    assert run_main(monkeypatch, "open", "--language", "pt") == 0
    assert runner.call_args.args[0] == [
        "ssh",
        "chise",
        "avatar-talk",
        "open --language pt --seat remote",
    ]
    take.assert_called_once_with()
    assert json.loads(capsys.readouterr().out)["seat"] == "remote"


@pytest.mark.parametrize(
    ("returncode", "seat", "attached"),
    [(1, "remote", False), (0, "room", False), (0, None, False), (0, "remote", True)],
)
def test_the_seat_is_taken_only_for_a_remote_conversation_not_yet_attached(
    monkeypatch, returncode, seat, attached
):
    chise_answers(monkeypatch, returncode, seat)
    monkeypatch.setattr(local_seat, "attached", lambda: attached)
    take = Mock()
    monkeypatch.setattr(local_seat, "take", take)
    assert remote_talk.open_here(["open"]) == returncode
    take.assert_not_called()


def test_a_seat_that_cannot_be_taken_fails_the_open(monkeypatch, capsys):
    monkeypatch.setattr(remote_talk, "user_is_here", lambda: True)
    chise_answers(monkeypatch)
    monkeypatch.setattr(local_seat, "attached", lambda: False)
    monkeypatch.setattr(local_seat, "take", Mock(side_effect=TimeoutError("no page")))
    assert run_main(monkeypatch, "open") == 1
    assert "no page" in capsys.readouterr().err


def test_closing_closes_the_conversation_then_leaves_the_seat(monkeypatch):
    order = Mock()
    order.run.return_value = SimpleNamespace(returncode=0)
    monkeypatch.setattr(remote_talk.subprocess, "run", order.run)
    monkeypatch.setattr(local_seat, "leave", order.leave)
    assert run_main(monkeypatch, "close") == 0
    assert [call[0] for call in order.mock_calls] == ["run", "leave"]


@pytest.mark.parametrize(
    ("output", "seat"),
    [
        ('{"open": true, "seat": "remote"}', "remote"),
        ('Character set\n{"open": true, "seat": "room"}\n', "room"),
        ('{"open": true}', None),
        ("not json", None),
        ("", None),
    ],
)
def test_the_seat_is_read_from_the_last_status_line(output, seat):
    assert remote_talk.reported_seat(output) == seat


@pytest.mark.parametrize(
    ("report", "seconds"),
    [
        ('    | |   "HIDIdleTime" = 2500000000\n', 2.5),
        ("no idle time here", float("inf")),
    ],
)
def test_idle_time_comes_from_the_input_system_report(monkeypatch, report, seconds):
    monkeypatch.setattr(
        remote_talk.subprocess, "run", Mock(return_value=SimpleNamespace(stdout=report))
    )
    assert remote_talk.seconds_since_input() == seconds


def test_taking_the_seat_tunnels_before_the_browser_and_waits_for_it(monkeypatch):
    order = Mock()
    for step in ("leave", "wait_for_tunnel", "open_browser", "wait_until_attached"):
        monkeypatch.setattr(local_seat, step, getattr(order, step))
    monkeypatch.setattr(local_seat.subprocess, "Popen", order.hold)
    local_seat.take()
    assert [call[0] for call in order.mock_calls] == [
        "leave",
        "hold",
        "wait_for_tunnel",
        "open_browser",
        "wait_until_attached",
    ]
    assert order.hold.call_args.kwargs["start_new_session"] is True


def test_leaving_ends_the_holder_before_it_can_close_a_newer_browser(monkeypatch):
    ended = Mock()
    monkeypatch.setattr(local_seat, "end_processes_matching", ended)
    local_seat.leave()
    assert ended.call_args_list[0].args == (local_seat.HOLDER_SCRIPT,)
    assert ended.call_count == 4
    assert local_seat.HOLDER_SCRIPT in local_seat.__file__


def test_a_seat_that_never_attaches_is_left_again(monkeypatch):
    leave = Mock()
    monkeypatch.setattr(local_seat, "leave", leave)
    monkeypatch.setattr(local_seat.subprocess, "Popen", Mock())
    monkeypatch.setattr(local_seat, "wait_for_tunnel", Mock())
    monkeypatch.setattr(local_seat, "open_browser", Mock())
    monkeypatch.setattr(
        local_seat, "wait_until_attached", Mock(side_effect=TimeoutError("late"))
    )
    with pytest.raises(TimeoutError):
        local_seat.take()
    assert leave.call_count == 2


def test_a_page_failure_ends_the_wait_with_its_reason(monkeypatch):
    monkeypatch.setattr(
        local_seat, "health", lambda: {"attached": False, "failure": "NotAllowedError"}
    )
    with pytest.raises(RuntimeError, match="NotAllowedError"):
        local_seat.wait_until_attached()


def test_a_page_that_never_attaches_times_out(monkeypatch):
    monkeypatch.setattr(local_seat, "health", lambda: None)
    monkeypatch.setattr(local_seat, "ATTACH_WAIT_SECONDS", 0)
    with pytest.raises(TimeoutError, match="microphone"):
        local_seat.wait_until_attached()
