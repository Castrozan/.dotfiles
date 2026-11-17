import shlex
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import listener_runtime
import pytest
import wake_boundaries
import wake_claim
from wake_fakes import armed_listener, boundaries
from wake_phrase import LiveSession

LOCAL_MEDEA = LiveSession("Medea", "w1:p1")
REMOTE_MEDEA = LiveSession("Medea", "w9:p4", "kira")
WORDS = "hey Medea, check the build"


@pytest.fixture(autouse=True)
def this_machine_is_chise(monkeypatch):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")


@pytest.fixture
def slept(monkeypatch):
    sleeper = Mock()
    monkeypatch.setattr(wake_boundaries.time, "sleep", sleeper)
    return sleeper


@pytest.fixture
def ran(monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(wake_boundaries.subprocess, "run", runner)
    return runner


def test_a_local_session_claims_directly_with_this_machines_room(
    monkeypatch, tmp_path, ran, slept
):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    assert wake_boundaries.claim_wake(LOCAL_MEDEA)
    assert wake_claim.claim_path(tmp_path, "w1:p1").read_text() == "chise"
    assert not ran.called and not slept.called


def test_a_remote_session_claims_through_ssh_after_the_head_start(ran, slept):
    order = Mock()
    order.attach_mock(slept, "sleep")
    order.attach_mock(ran, "run")
    assert wake_boundaries.claim_wake(REMOTE_MEDEA)
    assert [call[0] for call in order.mock_calls] == ["sleep", "run"]
    assert slept.call_args.args == (wake_boundaries.PEER_HEAD_START_SECONDS,)
    command = ran.call_args.args[0]
    assert command[-2] == "kira"
    assert shlex.split(command[-1]) == [
        "avatar-wake",
        "--claim",
        "w9:p4",
        "--room",
        "chise",
    ]
    assert ran.call_args.kwargs["timeout"] == wake_boundaries.PEER_CLAIM_TIMEOUT_SECONDS


@pytest.mark.parametrize("returncode", [1, 255])
def test_a_lost_claim_or_a_failed_ssh_means_lost(ran, slept, returncode):
    ran.return_value = SimpleNamespace(returncode=returncode)
    assert wake_boundaries.claim_wake(REMOTE_MEDEA) is False


@pytest.mark.parametrize(
    "failure", [subprocess.TimeoutExpired("ssh", 20), FileNotFoundError("ssh")]
)
def test_a_timeout_or_a_missing_ssh_means_lost(ran, slept, failure):
    ran.side_effect = failure
    assert wake_boundaries.claim_wake(REMOTE_MEDEA) is False


def test_the_mac_boundaries_claim_the_same_way_by_default(monkeypatch):
    monkeypatch.setattr(wake_boundaries.sys, "platform", "darwin")
    monkeypatch.setenv("AVATAR_AGENT_HOST", "kira")
    assert wake_boundaries.for_this_machine().claim_wake is wake_boundaries.claim_wake


def test_a_lost_claim_neither_prompts_nor_opens_and_says_so():
    fakes = boundaries(heard=WORDS, sessions=[LOCAL_MEDEA])
    fakes.claim_wake = Mock(return_value=False)
    armed_listener(fakes).hear(b"segment")
    fakes.claim_wake.assert_called_once_with(LOCAL_MEDEA)
    assert not fakes.prompt_now.called
    assert not fakes.notify_at_idle.called
    assert not fakes.open_conversation.called
    assert not fakes.hand_to.called
    fakes.report.assert_called_once_with("left Medea to another room")


def test_a_won_claim_is_taken_before_the_prompt():
    order = Mock()
    fakes = boundaries(
        heard=WORDS,
        sessions=[REMOTE_MEDEA],
        claim_wake=order.claim_wake,
        prompt_now=order.prompt_now,
    )
    order.claim_wake.return_value = True
    order.prompt_now.return_value = True
    armed_listener(fakes).hear(b"segment")
    assert [call[0] for call in order.mock_calls] == ["claim_wake", "prompt_now"]
    fakes.open_conversation.assert_called_once_with()


def test_a_dry_run_does_not_claim():
    fakes = boundaries(heard=WORDS, sessions=[REMOTE_MEDEA])
    armed_listener(fakes, dry_run=True).hear(b"segment")
    assert not fakes.claim_wake.called
    assert "would wake" in fakes.report.call_args.args[0]


def test_turning_to_a_servant_inside_a_conversation_takes_no_claim():
    fakes = boundaries(sessions=[LOCAL_MEDEA])
    listener = armed_listener(fakes)
    listener.turn_to({"sequence": 3, "speaker": "Lucas", "text": WORDS})
    assert fakes.prompt_now.called
    assert not fakes.claim_wake.called
