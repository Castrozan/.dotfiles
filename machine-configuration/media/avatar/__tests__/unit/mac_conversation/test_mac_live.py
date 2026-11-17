import json
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import live_opening
import mac_talk
import pytest
from conversation_addressee import Addressee
from conversation_state import ConversationPhase

PANE = "w4A:p1"
UNITS_THE_LIVE_VOICE_NEEDS = [
    "avatar-control-server.service",
    "avatar-renderer.service",
    "avatar-live.service",
]


@pytest.fixture
def this_mac(monkeypatch, tmp_path):
    mac = SimpleNamespace(
        steps=[],
        running=set(),
        phase=ConversationPhase.CLOSED,
        servant="Suzuka",
        tunnel=None,
        attached=True,
    )
    directory = tmp_path / "runtime"
    monkeypatch.setattr(
        mac_talk.listener_runtime, "runtime_directory", lambda: directory
    )
    monkeypatch.setenv(live_opening.PANE_ENVIRONMENT_VARIABLE, PANE)
    monkeypatch.setattr(mac_talk.local_seat, "health", lambda: mac.tunnel)
    monkeypatch.setattr(mac_talk.local_seat, "meeting_held", lambda: False)
    monkeypatch.setattr(mac_talk.local_seat, "leave", Mock())
    monkeypatch.setattr(mac_talk.mac_seat_client, "attached", lambda: mac.attached)
    monkeypatch.setattr(
        mac_talk.mac_seat_client, "hush", lambda: mac.steps.append("hush")
    )
    monkeypatch.setattr(
        mac_talk.mac_seat_client, "close_browser", lambda: mac.steps.append("browser")
    )
    monkeypatch.setattr(mac_talk.mac_stage, "answers", lambda port: True)
    monkeypatch.setattr(mac_talk.mac_stage.local_window, "hide", lambda: None)
    monkeypatch.setattr(
        mac_talk.mac_stage.user_units, "unit_active", lambda unit: unit in mac.running
    )

    def start_unit(unit):
        mac.steps.append(f"start {unit}")
        mac.running.add(unit)

    def stop_unit(unit):
        mac.steps.append(f"stop {unit}")
        mac.running.discard(unit)

    monkeypatch.setattr(mac_talk.listener_session, "start_unit", start_unit)
    monkeypatch.setattr(mac_talk.listener_session, "stop_unit", stop_unit)
    monkeypatch.setattr(
        mac_talk.conversation_state, "observe", lambda directory: mac.phase
    )

    def claim_the_floor(command, **options):
        mac.steps.append(command[0])
        if mac.servant:
            conversation_addressee.hand_to(directory, Addressee(PANE, mac.servant, 0))
        mac.phase = ConversationPhase.LIVE

    monkeypatch.setattr(live_opening.subprocess, "run", claim_the_floor)
    return mac


def test_opening_live_on_a_mac_runs_here_without_asking_the_avatar_host(
    this_mac, monkeypatch
):
    host = Mock(return_value=7)
    monkeypatch.setattr(mac_talk.remote_talk, "carry_out", host)
    assert mac_talk.carry_out(["open", "--live"]) == 0
    assert not host.called


def test_opening_live_starts_the_stage_and_the_live_agent_then_claims_the_floor(
    this_mac, capsys
):
    mac_talk.carry_out(["open", "--live"])
    assert this_mac.steps == [
        *(f"start {unit}" for unit in UNITS_THE_LIVE_VOICE_NEEDS),
        "avatar-claim-floor",
    ]
    assert json.loads(capsys.readouterr().out) == {
        "open": True,
        "live": True,
        "seat": "room",
        "last_heard": 0,
    }


def test_opening_live_waits_until_the_seat_page_attaches(this_mac, monkeypatch):
    this_mac.attached = False
    monkeypatch.setattr(mac_talk, "ATTACH_WAIT_SECONDS", -1)
    with pytest.raises(TimeoutError, match="did not attach"):
        mac_talk.carry_out(["open", "--live"])
    assert "avatar-claim-floor" not in this_mac.steps


def test_a_pane_without_a_servant_leaves_nothing_running(this_mac):
    this_mac.servant = None
    with pytest.raises(RuntimeError, match=live_opening.LIVE_NEEDS_A_SERVANT):
        mac_talk.carry_out(["open", "--live"])
    assert this_mac.running == set()
    assert this_mac.steps[-5:] == [
        "hush",
        "stop avatar-live.service",
        "browser",
        "stop avatar-control-server.service",
        "stop avatar-renderer.service",
    ]


def test_a_live_session_here_reports_live_and_closes_here(this_mac, capsys):
    this_mac.phase = ConversationPhase.LIVE
    mac_talk.carry_out(["status"])
    assert json.loads(capsys.readouterr().out)["live"] is True
    this_mac.steps.clear()
    assert mac_talk.carry_out(["close"]) == 0
    assert "hush" in this_mac.steps and "browser" in this_mac.steps
    assert json.loads(capsys.readouterr().out) == {"open": False}


def test_a_host_conversation_seated_at_this_mac_still_takes_live_to_the_host(
    this_mac, monkeypatch
):
    this_mac.tunnel = {"attached": True, "listening": True}
    host = Mock(return_value=7)
    monkeypatch.setattr(mac_talk.remote_talk, "carry_out", host)
    monkeypatch.setattr(
        mac_talk.remote_talk, "with_the_agent_that_receives_live_tasks", lambda a: a
    )
    assert mac_talk.carry_out(["open", "--live"]) == 7
    host.assert_called_once_with(["open", "--live"])
