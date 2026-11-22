import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import peer_sessions
import pytest
import wake_listener
from conversation_seat import Seat
from hypothesis import given
from hypothesis import strategies as st
from wake_fakes import armed_listener, boundaries
from wake_phrase import LiveSession

SERVANTS = st.sampled_from(["Voyager", "Medea", "Circe", "Ibaraki", "Sasaki"])
SESSIONS = st.lists(
    st.builds(LiveSession, SERVANTS, st.text("abc:p", min_size=1, max_size=4)),
    max_size=4,
)
SEATS = st.sampled_from([*Seat, None])
MEDEA = LiveSession("Medea", "w1:p1")


def listing(conversation_seat):
    payload = {"sessions": [], "conversation_seat": conversation_seat}
    return SimpleNamespace(stdout=json.dumps(payload), returncode=0)


def refreshed(peer_hosts, run):
    peers = peer_sessions.PeerSessions(
        peer_hosts, run, start_worker=lambda work: work()
    )
    peers.discord_call_host()
    return peers


def test_the_sessions_flag_prints_this_machines_listing_as_one_json_object(
    monkeypatch, capsys
):
    monkeypatch.setattr(sys, "argv", ["avatar-wake", "--sessions"])
    monkeypatch.setattr(
        peer_sessions,
        "live_sessions",
        lambda: [LiveSession("Voyager", "w:p1"), LiveSession("Medea", "w:p2")],
    )
    monkeypatch.setattr(peer_sessions, "open_seat", lambda directory: Seat.DISCORD)
    monkeypatch.setattr(wake_listener, "run", Mock(side_effect=AssertionError))
    wake_listener.main()
    assert json.loads(capsys.readouterr().out) == {
        "sessions": [
            {"servant": "Voyager", "pane": "w:p1"},
            {"servant": "Medea", "pane": "w:p2"},
        ],
        "conversation_seat": "discord",
    }


@given(sessions=SESSIONS, seat=SEATS)
def test_a_machines_listing_is_read_back_by_its_peer_unchanged(sessions, seat):
    run = Mock(
        return_value=SimpleNamespace(
            stdout=peer_sessions.listing_of(sessions, seat), returncode=0
        )
    )
    read = peer_sessions.sessions_of_peer("kira", run)
    assert read.sessions == [
        LiveSession(session.servant, session.pane, "kira") for session in sessions
    ]
    assert read.conversation_seat == seat


@pytest.mark.parametrize(
    ("seat", "host"),
    [("discord", "kira"), ("room", None), ("remote", None), (None, None)],
)
def test_a_peer_reporting_a_discord_seat_is_the_discord_call_host(seat, host):
    peers = refreshed(["kira"], Mock(return_value=listing(seat)))
    assert peers.discord_call_host() == host


def test_the_discord_call_host_is_the_peer_that_reports_it():
    def run(command, **_):
        return listing("discord" if command[-3] == "rin" else None)

    assert refreshed(["kira", "rin"], run).discord_call_host() == "rin"


def test_the_discord_call_host_never_waits_on_a_peer():
    run = Mock()
    started = []
    peers = peer_sessions.PeerSessions(["kira"], run, start_worker=started.append)
    assert peers.discord_call_host() is None
    assert peers.discord_call_host() is None
    run.assert_not_called()
    assert len(started) == 1


def test_a_peer_that_stops_reporting_a_discord_seat_is_forgotten():
    seats = ["discord", None]
    run = Mock(side_effect=lambda *_, **__: listing(seats.pop(0)))
    clock = SimpleNamespace(now=0.0)
    started = []
    peers = peer_sessions.PeerSessions(
        ["kira"], run, clock=lambda: clock.now, start_worker=started.append
    )
    peers.discord_call_host()
    started.pop()()
    assert peers.discord_call_host() == "kira"
    clock.now = peer_sessions.PEER_REFRESH_SECONDS
    peers.discord_call_host()
    started.pop()()
    assert peers.discord_call_host() is None


def test_peers_are_refreshed_at_most_every_twenty_seconds():
    assert peer_sessions.PEER_REFRESH_SECONDS == 20


def test_the_wake_leaves_the_servant_to_a_discord_call_at_a_peer():
    fakes = boundaries(
        "hey Medea, check the build",
        sessions=(MEDEA,),
        discord_call_host=Mock(return_value="chise"),
    )
    armed_listener(fakes).hear(b"segment")
    fakes.report.assert_any_call("left Medea to the Discord call on chise")
    fakes.claim_wake.assert_not_called()
    fakes.prompt_now.assert_not_called()
    fakes.open_conversation.assert_not_called()
    fakes.hand_to.assert_not_called()


def test_the_wake_opens_a_conversation_when_no_peer_is_in_a_discord_call():
    fakes = boundaries("hey Medea, check the build", sessions=(MEDEA,))
    armed_listener(fakes).hear(b"segment")
    fakes.open_conversation.assert_called_once_with()
    fakes.prompt_now.assert_called_once()
    fakes.hand_to.assert_called_once()
