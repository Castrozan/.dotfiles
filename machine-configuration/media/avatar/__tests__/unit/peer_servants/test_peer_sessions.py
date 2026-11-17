import json
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import peer_sessions
import pytest
import wake_listener
from hypothesis import given
from hypothesis import strategies as st
from wake_phrase import LiveSession

SERVANTS = st.sampled_from(["Voyager", "Medea", "Circe", "Ibaraki", "Sasaki"])
LOCAL = st.lists(
    st.builds(LiveSession, SERVANTS, st.text("abc:p", min_size=1, max_size=4)),
    max_size=4,
)
PEERS = st.dictionaries(
    st.sampled_from(["kira", "rin"]),
    st.lists(
        st.fixed_dictionaries({"servant": SERVANTS, "pane": st.just("w:p9")}),
        max_size=4,
    ),
)


def listing(entries):
    return SimpleNamespace(stdout=json.dumps(entries), returncode=0)


def runner_for(peers):
    return Mock(side_effect=lambda command, **_: listing(peers[command[-3]]))


def test_a_peer_is_asked_over_ssh_with_a_bounded_wait():
    run = Mock(return_value=listing([]))
    peer_sessions.sessions_everywhere([], ["kira"], run)
    assert run.call_args.args[0] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "kira",
        "avatar-wake",
        "--sessions",
    ]
    assert run.call_args.kwargs["timeout"] == 10


def test_peer_sessions_carry_the_host_they_live_on():
    run = Mock(return_value=listing([{"servant": "Medea", "pane": "w1:p2"}]))
    assert peer_sessions.sessions_everywhere([], ["kira"], run) == [
        LiveSession("Medea", "w1:p2", "kira")
    ]


def test_local_sessions_stay_without_a_host():
    local = [LiveSession("Voyager", "w:p1")]
    assert peer_sessions.sessions_everywhere(local, [], Mock()) == local


@given(local=LOCAL, peers=PEERS)
def test_every_servant_is_heard_once_and_the_local_session_wins(local, peers):
    merged = peer_sessions.sessions_everywhere(local, list(peers), runner_for(peers))
    local_servants = {session.servant for session in local}
    assert merged[: len(local)] == local
    remote = merged[len(local) :]
    assert all(session.host in peers for session in remote)
    assert not {session.servant for session in remote} & local_servants
    expected = sum(
        entry["servant"] not in local_servants
        for entries in peers.values()
        for entry in entries
    )
    assert len(remote) == expected


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired("ssh", 10),
        OSError("no ssh"),
        subprocess.CalledProcessError(255, "ssh"),
        SimpleNamespace(stdout="", returncode=255),
        SimpleNamespace(stdout="not json", returncode=0),
        SimpleNamespace(stdout='{"servant": "Medea"}', returncode=0),
        SimpleNamespace(stdout='[{"servant": "Medea"}]', returncode=0),
        SimpleNamespace(stdout="[7]", returncode=0),
    ],
)
def test_an_unreachable_peer_contributes_nothing_and_never_raises(failure):
    local = [LiveSession("Voyager", "w:p1")]
    if isinstance(failure, BaseException):
        run = Mock(side_effect=failure)
    else:
        run = Mock(return_value=failure)
    assert peer_sessions.sessions_everywhere(local, ["kira"], run) == local


def test_a_failing_peer_does_not_hide_the_others():
    def run(command, **_):
        if command[-3] == "kira":
            raise subprocess.TimeoutExpired("ssh", 10)
        return listing([{"servant": "Medea", "pane": "w1:p2"}])

    assert peer_sessions.sessions_everywhere([], ["kira", "rin"], run) == [
        LiveSession("Medea", "w1:p2", "rin")
    ]


def test_the_sessions_flag_prints_this_machines_sessions_as_one_json_list(
    monkeypatch, capsys
):
    monkeypatch.setattr(sys, "argv", ["avatar-wake", "--sessions"])
    monkeypatch.setattr(
        wake_listener,
        "live_sessions",
        lambda: [LiveSession("Voyager", "w:p1"), LiveSession("Medea", "w:p2")],
    )
    monkeypatch.setattr(wake_listener, "run", Mock(side_effect=AssertionError))
    wake_listener.main()
    assert json.loads(capsys.readouterr().out) == [
        {"servant": "Voyager", "pane": "w:p1"},
        {"servant": "Medea", "pane": "w:p2"},
    ]
