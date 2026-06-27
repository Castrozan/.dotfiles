import sys
from pathlib import Path

import pytest

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import settings


def test_resolve_bridge_settings_uses_defaults_for_empty_environment():
    resolved_settings = settings.resolve_bridge_settings({})
    assert resolved_settings.listen_address == "127.0.0.1"
    assert resolved_settings.listen_port == 8787
    assert resolved_settings.session_command == ["/bin/sh", "-il"]
    assert resolved_settings.allowed_request_origin == "https://lucaszanoni.com"


def test_resolve_bridge_settings_reads_overrides_from_environment():
    resolved_settings = settings.resolve_bridge_settings(
        {
            "COCKPIT_SESSION_BRIDGE_LISTEN_ADDRESS": "0.0.0.0",
            "COCKPIT_SESSION_BRIDGE_LISTEN_PORT": "9001",
            "COCKPIT_SESSION_BRIDGE_COMMAND_JSON": '["/run/current-system/sw/bin/fish", "-l"]',
            "COCKPIT_SESSION_BRIDGE_ALLOWED_ORIGIN": "https://example.test",
            "COCKPIT_SESSION_BRIDGE_TMUX_PATH": "/run/current-system/sw/bin/tmux",
        }
    )
    assert resolved_settings.listen_address == "0.0.0.0"
    assert resolved_settings.listen_port == 9001
    assert resolved_settings.session_command == [
        "/run/current-system/sw/bin/fish",
        "-l",
    ]
    assert resolved_settings.allowed_request_origin == "https://example.test"
    assert (
        resolved_settings.cockpit_tmux_executable_path
        == "/run/current-system/sw/bin/tmux"
    )


def test_parse_session_command_rejects_non_string_entries():
    with pytest.raises(ValueError):
        settings.parse_session_command('["bash", 7]')


def test_parse_session_command_rejects_empty_array():
    with pytest.raises(ValueError):
        settings.parse_session_command("[]")


def test_is_request_origin_allowed_requires_exact_match_when_configured():
    assert settings.is_request_origin_allowed(
        "https://lucaszanoni.com", "https://lucaszanoni.com"
    )
    assert not settings.is_request_origin_allowed(
        "https://evil.test", "https://lucaszanoni.com"
    )


def test_is_request_origin_allowed_allows_any_when_unset():
    assert settings.is_request_origin_allowed("", "")
    assert settings.is_request_origin_allowed("https://anything.test", "")


def test_parse_owner_control_message_reads_a_resize_request():
    parsed_window_size = settings.parse_owner_control_message(
        '{"type": "resize", "columns": 180, "rows": 48}'
    )
    assert parsed_window_size == settings.PseudoterminalWindowSizeRequest(
        columns=180, rows=48
    )


def test_parse_owner_control_message_ignores_non_json_keystroke_text():
    assert settings.parse_owner_control_message("ls -la\n") is None


def test_parse_owner_control_message_ignores_unknown_control_types():
    assert (
        settings.parse_owner_control_message('{"type": "paste", "data": "x"}') is None
    )


def test_parse_owner_control_message_rejects_non_positive_or_non_integer_dimensions():
    assert (
        settings.parse_owner_control_message('{"type":"resize","columns":0,"rows":40}')
        is None
    )
    assert (
        settings.parse_owner_control_message('{"type":"resize","columns":80,"rows":-1}')
        is None
    )
    assert (
        settings.parse_owner_control_message(
            '{"type":"resize","columns":80.5,"rows":40}'
        )
        is None
    )
    assert (
        settings.parse_owner_control_message(
            '{"type":"resize","columns":true,"rows":40}'
        )
        is None
    )


def test_parse_owner_control_message_rejects_dimensions_beyond_the_maximum():
    assert (
        settings.parse_owner_control_message(
            '{"type":"resize","columns":99999,"rows":40}'
        )
        is None
    )
