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
