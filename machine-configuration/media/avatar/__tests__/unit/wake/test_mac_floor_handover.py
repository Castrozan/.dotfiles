import json
from types import SimpleNamespace
from unittest.mock import Mock

import mac_wake_boundaries
import pytest
import wake_listener
from avatar_host_runner import ran, remote_command
from conversation_addressee import Addressee
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")
NAMING_TURN = {
    "sequence": 9,
    "time": 1.5,
    "source": "human",
    "text": "Olá Voyager, status",
    "speaker": "Lucas",
    "turn_finished": True,
}


def test_the_addressee_is_the_holder_when_one_of_this_macs_sessions_holds_the_floor(
    monkeypatch, on_a_mac
):
    holder = Addressee(VOYAGER.pane, VOYAGER.servant, 7, "kira")
    runner = ran(
        monkeypatch,
        json.dumps(
            {"pane": holder.pane, "servant": holder.servant, "heard_through": 7}
            | {"host": "kira"}
        ),
    )
    assert on_a_mac.addressee() == holder
    assert remote_command(runner) == "avatar-listen addressee"


@pytest.mark.parametrize("host", [None, "another-mac"])
def test_a_floor_held_by_another_machines_session_is_not_held_here(
    monkeypatch, on_a_mac, host
):
    ran(
        monkeypatch,
        json.dumps(
            {
                "pane": VOYAGER.pane,
                "servant": "Voyager",
                "heard_through": 3,
                "host": host,
            }
        ),
    )
    assert on_a_mac.addressee() is None


def test_nobody_holding_the_floor_is_no_addressee(monkeypatch, on_a_mac):
    ran(monkeypatch, "null")
    assert on_a_mac.addressee() is None


def test_the_handover_carries_how_far_the_room_was_heard(monkeypatch, on_a_mac):
    runner = ran(monkeypatch, "")
    on_a_mac.hand_to(Addressee(VOYAGER.pane, VOYAGER.servant, 12))
    assert remote_command(runner) == (
        "avatar-claim-floor --agent kira:wW:pPZ --heard-through 12"
    )


def test_naming_a_session_of_this_mac_hands_it_the_floor_at_the_heard_entry(
    monkeypatch, on_a_mac
):
    runner = Mock(
        side_effect=[
            SimpleNamespace(stdout=b"null", returncode=0),
            SimpleNamespace(stdout=b"", returncode=0),
            SimpleNamespace(
                stdout=json.dumps(
                    {"listening": True, "purpose": "conversation"}
                ).encode(),
                returncode=0,
            ),
        ]
    )
    monkeypatch.setattr(mac_wake_boundaries.subprocess, "run", runner)
    on_a_mac.sessions = Mock(return_value=[VOYAGER])
    on_a_mac.report = Mock()
    on_a_mac.prompt_now = Mock(return_value=True)
    wake = wake_listener.WakeListener(on_a_mac, dry_run=False)
    wake.turn_to(NAMING_TURN)
    commands = [call.args[0][-1] for call in runner.call_args_list]
    assert commands == [
        "avatar-listen addressee",
        "avatar-claim-floor --agent kira:wW:pPZ --heard-through 9",
        "avatar-listen status",
    ]
    on_a_mac.prompt_now.assert_called_once()
