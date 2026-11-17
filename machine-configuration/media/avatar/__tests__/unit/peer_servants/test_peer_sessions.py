import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import peer_sessions
import pytest
from hypothesis import given
from hypothesis import strategies as st
from wake_phrase import LiveSession

SERVANTS = st.sampled_from(["Voyager", "Medea", "Circe", "Ibaraki", "Sasaki"])
LOCAL = st.lists(
    st.builds(LiveSession, SERVANTS, st.text("abc:p", min_size=1, max_size=4)),
    max_size=4,
)
REMOTE = st.lists(
    st.builds(LiveSession, SERVANTS, st.just("w:p9"), st.sampled_from(["kira", "rin"])),
    max_size=4,
)
MEDEA_AT_KIRA = LiveSession("Medea", "w1:p2", "kira")


def listing(entries, conversation_seat=None):
    payload = {"sessions": entries, "conversation_seat": conversation_seat}
    return SimpleNamespace(stdout=json.dumps(payload), returncode=0)


def refreshed(peer_hosts, run):
    peers = peer_sessions.PeerSessions(
        peer_hosts, run, start_worker=lambda work: work()
    )
    peers.known()
    return peers.known()


def test_a_peer_is_asked_over_ssh_with_a_bounded_wait():
    run = Mock(return_value=listing([]))
    refreshed(["kira"], run)
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
    assert refreshed(["kira"], run) == [MEDEA_AT_KIRA]


def test_local_sessions_stay_without_a_host():
    local = [LiveSession("Voyager", "w:p1")]
    assert peer_sessions.sessions_everywhere(local, []) == local


@given(local=LOCAL, remote=REMOTE)
def test_every_servant_is_heard_once_and_the_local_session_wins(local, remote):
    merged = peer_sessions.sessions_everywhere(local, remote)
    local_servants = {session.servant for session in local}
    assert merged[: len(local)] == local
    assert merged[len(local) :] == [
        session for session in remote if session.servant not in local_servants
    ]


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
        SimpleNamespace(stdout='{"sessions": []}', returncode=0),
        SimpleNamespace(
            stdout='{"sessions": [{"servant": "Medea"}], "conversation_seat": null}',
            returncode=0,
        ),
        SimpleNamespace(stdout='[{"servant": "Medea", "pane": "w1:p2"}]', returncode=0),
    ],
)
def test_an_unreachable_peer_contributes_nothing_and_never_raises(failure):
    if isinstance(failure, BaseException):
        run = Mock(side_effect=failure)
    else:
        run = Mock(return_value=failure)
    assert refreshed(["kira"], run) == []


def test_a_failing_peer_does_not_hide_the_others():
    def run(command, **_):
        if command[-3] == "kira":
            raise subprocess.TimeoutExpired("ssh", 10)
        return listing([{"servant": "Medea", "pane": "w1:p2"}])

    assert refreshed(["kira", "rin"], run) == [LiveSession("Medea", "w1:p2", "rin")]


def test_known_returns_at_once_while_the_listing_is_pending():
    run = Mock()
    started = []
    peers = peer_sessions.PeerSessions(["kira"], run, start_worker=started.append)
    assert peers.known() == []
    assert peers.known() == []
    run.assert_not_called()
    assert len(started) == 1


def test_the_cache_is_replaced_after_a_refresh():
    entries = [{"servant": "Medea", "pane": "w1:p2"}]
    run = Mock(side_effect=lambda *_, **__: listing(entries))
    clock = SimpleNamespace(now=0.0)
    started = []
    peers = peer_sessions.PeerSessions(
        ["kira"], run, clock=lambda: clock.now, start_worker=started.append
    )
    peers.known()
    started.pop()()
    assert peers.known() == [MEDEA_AT_KIRA]
    entries[:] = [{"servant": "Circe", "pane": "w1:p3"}]
    clock.now = peer_sessions.PEER_REFRESH_SECONDS
    assert peers.known() == [MEDEA_AT_KIRA]
    started.pop()()
    assert peers.known() == [LiveSession("Circe", "w1:p3", "kira")]


def test_a_refresh_starts_at_most_once_per_interval_and_never_overlaps():
    clock = SimpleNamespace(now=0.0)
    started = []
    peers = peer_sessions.PeerSessions(
        ["kira"], Mock(), clock=lambda: clock.now, start_worker=started.append
    )
    peers.known()
    started.pop()()
    clock.now = peer_sessions.PEER_REFRESH_SECONDS - 1
    peers.known()
    assert not started
    clock.now = peer_sessions.PEER_REFRESH_SECONDS
    peers.known()
    clock.now = 3 * peer_sessions.PEER_REFRESH_SECONDS
    peers.known()
    assert len(started) == 1, "a refresh still running is never started twice"


def test_no_peer_hosts_never_start_a_worker():
    started = []
    peers = peer_sessions.PeerSessions([], Mock(), start_worker=started.append)
    assert peers.known() == []
    assert not started
