import sys
from pathlib import Path

import pytest

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "jarvis_session_bridge"
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
            "JARVIS_SESSION_BRIDGE_LISTEN_ADDRESS": "0.0.0.0",
            "JARVIS_SESSION_BRIDGE_LISTEN_PORT": "9001",
            "JARVIS_SESSION_BRIDGE_COMMAND_JSON": '["/run/current-system/sw/bin/fish", "-l"]',
            "JARVIS_SESSION_BRIDGE_ALLOWED_ORIGIN": "https://example.test",
        }
    )
    assert resolved_settings.listen_address == "0.0.0.0"
    assert resolved_settings.listen_port == 9001
    assert resolved_settings.session_command == [
        "/run/current-system/sw/bin/fish",
        "-l",
    ]
    assert resolved_settings.allowed_request_origin == "https://example.test"


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
