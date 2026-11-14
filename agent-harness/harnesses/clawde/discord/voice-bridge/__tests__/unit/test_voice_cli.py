import json
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies as st

import silver_voice_cli


@pytest.mark.parametrize("arguments", [[], ["--default"], ["work-peer"]])
def test_agent_selection_uses_the_conductor_not_the_discord_socket(
    monkeypatch, arguments
):
    request = Mock(return_value={"backend": "hermes"})
    monkeypatch.setattr(silver_voice_cli, "request_once", request)
    parsed = silver_voice_cli.parse_arguments(["agent", *arguments])
    assert parsed.handler(parsed) == {"backend": "hermes"}
    payload = request.call_args.kwargs
    assert payload["socket_path"] == silver_voice_cli.CONDUCTOR_SOCKET
    assert payload["command"] == ("agent" if arguments else "status")
    if arguments:
        assert payload["default"] is (arguments == ["--default"])
        assert payload["target"] == (
            None if arguments == ["--default"] else "work-peer"
        )


def test_default_and_target_cannot_be_selected_together():
    with pytest.raises(SystemExit):
        silver_voice_cli.parse_arguments(["agent", "work-peer", "--default"])


@pytest.mark.parametrize(
    "arguments", [["catalog"], ["character", "Second"], ["model", "eleven_flash_v2_5"]]
)
def test_presentation_commands_use_the_existing_bridge(monkeypatch, arguments):
    request = Mock(return_value={"ok": True})
    monkeypatch.setattr(silver_voice_cli, "request_running_bridge", request)
    parsed = silver_voice_cli.parse_arguments(arguments)
    assert parsed.handler(parsed) == {"ok": True}
    expected = {"command": arguments[0]}
    if len(arguments) == 2:
        expected["name"] = arguments[1]
    request.assert_called_once_with(**expected)


@given(st.text())
def test_speech_payload_preserves_unicode_text(text):
    connection = Mock()
    silver_voice_cli.send_request(
        connection, command="speak", text=text, language="en-us"
    )
    message = json.loads(connection.sendall.call_args.args[0])
    assert message == {"command": "speak", "text": text, "language": "en-us"}


def test_missing_conductor_reports_an_error_without_starting_a_service(monkeypatch):
    monkeypatch.setattr(
        silver_voice_cli, "request_once", Mock(side_effect=FileNotFoundError)
    )
    control = Mock()
    monkeypatch.setattr(silver_voice_cli, "control_bridge_service", control)
    arguments = silver_voice_cli.parse_arguments(["agent"])
    assert arguments.handler(arguments) == {"error": "conductor_not_running"}
    control.assert_not_called()
