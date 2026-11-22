from unittest.mock import Mock

import pytest

import silver_voice_cli
import voice_control
import voice_setup


@pytest.mark.parametrize(
    "command",
    ["speak", "follow", "catalog", "character", "model", "agent", "meeting-start"],
)
def test_the_conversation_commands_of_the_old_pipeline_are_gone(command):
    with pytest.raises(SystemExit):
        silver_voice_cli.parse_arguments([command])


def test_join_no_longer_accepts_an_answering_agent():
    with pytest.raises(SystemExit):
        silver_voice_cli.parse_arguments(["join", "--agent", "work-peer"])


@pytest.mark.parametrize(
    ("arguments", "preferred", "follows"),
    [
        (["join"], "primary", False),
        (["join", "--bot", "second"], "second", False),
        (["join-me", "--follow-listener"], "primary", True),
    ],
)
def test_join_starts_the_bridge_and_joins_without_selecting_a_conversation(
    monkeypatch, arguments, preferred, follows
):
    monkeypatch.setattr(voice_setup, "meeting_runtime_active", lambda: False)
    service = Mock()
    request = Mock(return_value={"joined": True})
    monkeypatch.setattr(voice_control, "control_bridge_service", service)
    monkeypatch.setattr(voice_control, "request_join", request)
    parsed = silver_voice_cli.parse_arguments(arguments)
    assert parsed.handler(parsed) == {"joined": True}
    service.assert_called_once_with("start")
    request.assert_called_once_with(preferred, follows)


def test_join_is_refused_while_meeting_devices_are_active(monkeypatch):
    monkeypatch.setattr(voice_setup, "meeting_runtime_active", lambda: True)
    service = Mock()
    monkeypatch.setattr(voice_control, "control_bridge_service", service)
    parsed = silver_voice_cli.parse_arguments(["join"])
    assert parsed.handler(parsed) == {
        "error": "meeting_devices_active_leave_meeting_before_discord"
    }
    service.assert_not_called()


def join_replies(monkeypatch, replies, clock=None):
    request = Mock(side_effect=replies)
    monkeypatch.setattr(voice_control, "request_once", request)
    monkeypatch.setattr(voice_control.time, "sleep", lambda seconds: None)
    if clock is not None:
        monkeypatch.setattr(voice_control.time, "monotonic", clock)
    return request


def test_join_waits_while_the_bridge_bots_are_still_connecting(monkeypatch):
    request = join_replies(
        monkeypatch,
        [
            {"error": "bridge_not_ready"},
            {"error": "bridge_not_ready"},
            {"joined": True},
        ],
    )
    assert voice_control.request_join("primary") == {"joined": True}
    assert request.call_count == 3


def test_join_stops_waiting_for_the_bots_at_its_deadline(monkeypatch):
    ticks = iter(range(0, 1000, 10))
    request = join_replies(
        monkeypatch,
        [{"error": "bridge_not_ready"}] * 100,
        clock=lambda: next(ticks),
    )
    assert voice_control.request_join("primary") == {"error": "bridge_not_ready"}
    assert request.call_count <= voice_control.JOIN_DEADLINE_SECONDS // 10 + 1


@pytest.mark.parametrize(
    "error",
    [
        "listener_not_in_allowed_voice_channel",
        "no_eligible_available_bot_for_listener",
    ],
)
def test_join_returns_a_refusal_that_waiting_cannot_fix_at_once(monkeypatch, error):
    request = join_replies(monkeypatch, [{"error": error}])
    assert voice_control.request_join("primary") == {"error": error}
    request.assert_called_once()
