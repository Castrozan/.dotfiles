import shlex
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import room_reach
from hypothesis import given
from hypothesis import strategies as st

ARGUMENTS = st.lists(
    st.text(st.characters(blacklist_characters="\x00", blacklist_categories=["Cs"])),
    max_size=5,
)
PANES = st.text(
    st.characters(blacklist_characters="\x00", blacklist_categories=["Cs"]),
    min_size=1,
    max_size=8,
)
HARD_ARGUMENTS = [
    "say",
    "hello world",
    'it\'s "quoted" $HOME `date`\nnew line',
    "",
    "*",
]


def forwarded(arguments, environment, run=None, this_host="chise"):
    run = run or Mock(return_value=SimpleNamespace(returncode=0))
    code = room_reach.forwarded_to_the_room(arguments, environment, this_host, run)
    return code, run


@given(arguments=ARGUMENTS, pane=PANES)
def test_the_remote_command_carries_exactly_the_original_arguments(arguments, pane):
    _, run = forwarded(arguments, {"AVATAR_ROOM": "kira", "HERDR_PANE_ID": pane})
    remote = run.call_args.args[0][-1]
    assert shlex.split(remote) == [
        "env",
        f"HERDR_PANE_ID={pane}",
        "avatar-talk",
        *arguments,
    ]


@given(arguments=ARGUMENTS)
def test_without_a_pane_the_remote_command_has_no_identity(arguments):
    _, run = forwarded(arguments, {"AVATAR_ROOM": "kira"})
    assert shlex.split(run.call_args.args[0][-1]) == ["avatar-talk", *arguments]


def test_a_quoted_sentence_reaches_the_room_as_one_argument():
    _, run = forwarded(HARD_ARGUMENTS, {"AVATAR_ROOM": "kira", "HERDR_PANE_ID": "w:p1"})
    assert shlex.split(run.call_args.args[0][-1])[3:] == HARD_ARGUMENTS


def test_the_command_goes_over_ssh_to_the_room_with_the_longest_seat_wait():
    _, run = forwarded(["follow"], {"AVATAR_ROOM": "kira"})
    assert run.call_args.args[0][:-1] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "kira",
    ]
    assert run.call_args.kwargs["timeout"] == 12 * 60 * 60
    assert "stdout" not in run.call_args.kwargs, "follow streams through the terminal"


@given(arguments=ARGUMENTS)
def test_the_room_machine_acts_locally(arguments):
    _, run = forwarded(arguments, {"AVATAR_ROOM": "kira", "HERDR_PANE_ID": "w:p1"})
    assert "AVATAR_ROOM" not in run.call_args.args[0][-1]


@pytest.mark.parametrize(
    "environment",
    [{}, {"AVATAR_ROOM": ""}, {"AVATAR_ROOM": "chise"}],
)
def test_no_forwarding_without_another_room(environment):
    code, run = forwarded(["say", "hi"], environment)
    assert code is None
    run.assert_not_called()


@pytest.mark.parametrize("code", [0, 1, 7, 255])
def test_the_return_code_of_the_room_is_passed_through(code):
    run = Mock(return_value=SimpleNamespace(returncode=code))
    assert forwarded(["say"], {"AVATAR_ROOM": "kira"}, run)[0] == code


def test_a_missing_ssh_is_reported_as_a_failure(monkeypatch, capsys):
    monkeypatch.setenv("AVATAR_ROOM", "kira")
    monkeypatch.setattr(
        room_reach.subprocess, "run", Mock(side_effect=OSError("no ssh"))
    )
    assert room_reach.forwarded_from_this_machine(["say"]) == 1
    assert "no ssh" in capsys.readouterr().err


def test_this_host_is_the_agent_host_or_the_short_machine_name(monkeypatch):
    assert room_reach.this_host({"AVATAR_AGENT_HOST": "kira"}) == "kira"
    monkeypatch.setattr(room_reach.socket, "gethostname", lambda: "chise.lan")
    assert room_reach.this_host({}) == "chise"
