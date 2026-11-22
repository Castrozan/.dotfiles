import fcntl
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import listener_runtime
import pytest
import wake_claim
from conversation_addressee import Addressee


def test_a_second_microphone_cannot_steal_an_active_local_conversation_after_the_lease(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(listener_runtime, "listening", Mock(return_value=True))
    conversation_addressee.hand_to(tmp_path, Addressee("w:p1", "Ishtar", 0))
    assert wake_claim.claim(tmp_path, "w:p1", "chise", 1000)
    assert not wake_claim.claim(
        tmp_path, "w:p1", "kira", 1000 + wake_claim.CLAIM_SECONDS + 1
    )


def test_an_active_conversation_does_not_block_a_different_agent(monkeypatch, tmp_path):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(listener_runtime, "listening", Mock(return_value=True))
    conversation_addressee.hand_to(tmp_path, Addressee("w:p1", "Ishtar", 0))
    assert wake_claim.claim(tmp_path, "w:p2", "kira", 1000)


def test_an_inactive_listener_does_not_pin_its_old_conversation(monkeypatch, tmp_path):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(listener_runtime, "listening", Mock(return_value=False))
    conversation_addressee.hand_to(tmp_path, Addressee("w:p1", "Ishtar", 0))
    assert wake_claim.claim(tmp_path, "w:p1", "kira", 1000)


@pytest.mark.parametrize(
    ("conversation", "accepted"),
    [
        ({"host": "chise", "pane": "w:p1"}, False),
        ({"host": "rin", "pane": "w:p1"}, True),
        ({"host": "chise", "pane": "w:p2"}, True),
        (None, True),
    ],
)
def test_only_the_same_session_active_in_a_remote_room_keeps_its_route(
    monkeypatch, tmp_path, conversation, accepted
):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    runner = Mock(return_value=SimpleNamespace(stdout=json.dumps(conversation)))
    monkeypatch.setattr(wake_claim.subprocess, "run", runner)
    assert wake_claim.claim(tmp_path, "w:p1", "rin", 1000)
    assert wake_claim.claim(tmp_path, "w:p1", "kira", 1011) is accepted
    assert runner.call_count == 1
    assert runner.call_args.kwargs["timeout"] == wake_claim.ROOM_QUERY_SECONDS
    assert runner.call_args.args[0][-2:] == ["rin", "avatar-wake --conversation"]


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired("ssh", 5),
        subprocess.CalledProcessError(255, "ssh"),
        OSError("unreachable"),
    ],
)
def test_an_unreachable_previous_room_never_silently_changes_the_route(
    monkeypatch, tmp_path, failure
):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(wake_claim.subprocess, "run", Mock(side_effect=failure))
    assert wake_claim.claim(tmp_path, "w:p1", "rin", 1000)
    before = wake_claim.claim_path(tmp_path, "w:p1").read_text()
    with pytest.raises(type(failure)):
        wake_claim.claim(tmp_path, "w:p1", "kira", 1011)
    assert wake_claim.claim_path(tmp_path, "w:p1").read_text() == before


@pytest.mark.parametrize("answer", ["", "{}", "[]", '{"conversation": false}'])
def test_a_malformed_room_report_does_not_authorize_a_handoff(
    monkeypatch, tmp_path, answer
):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(
        wake_claim.subprocess, "run", Mock(return_value=SimpleNamespace(stdout=answer))
    )
    assert wake_claim.claim(tmp_path, "w:p1", "rin", 1000)
    with pytest.raises(ConnectionError):
        wake_claim.claim(tmp_path, "w:p1", "kira", 1011)


def test_same_pane_numbers_on_different_agent_hosts_are_independent(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(listener_runtime, "listening", Mock(return_value=True))
    conversation_addressee.hand_to(tmp_path, Addressee("w:p1", "Ishtar", 0, "rin"))
    assert wake_claim.claim(tmp_path, "w:p1", "kira", 1000)


def test_contending_wakes_do_not_queue_behind_a_peer_lookup(monkeypatch, tmp_path):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    path = wake_claim.claim_path(tmp_path, "w:p1")
    path.parent.mkdir()
    with path.open("a+") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        assert not wake_claim.claim(tmp_path, "w:p1", "kira", 1000)
