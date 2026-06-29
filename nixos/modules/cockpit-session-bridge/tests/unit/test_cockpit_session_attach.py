import dataclasses
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_tmux_commands
import server
import settings

TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"


class _FakeWebsocketRequest:
    def __init__(self, request_path):
        self.path = request_path


class _FakeWebsocketConnection:
    def __init__(self, request_path):
        self.request = _FakeWebsocketRequest(request_path)


def _attach_settings():
    return settings.CockpitSessionBridgeSettings(
        listen_address="127.0.0.1",
        listen_port=8787,
        session_command=["/bin/sh", "-il"],
        allowed_request_origin="https://lucaszanoni.com",
        terminal_type="xterm-256color",
        cockpit_tmux_executable_path=TMUX_EXECUTABLE_PATH,
        cockpit_tmux_enumeration_socket_name="",
        cockpit_tmux_mutation_socket_name="cockpit",
    )


def test_read_session_attach_target_reads_the_session_name_from_the_query():
    assert (
        settings.read_session_attach_target(
            "/cockpit/jarvis-session/?sessionName=dotfiles&windowIdentifier=@1"
        )
        == "dotfiles"
    )


def test_read_session_attach_target_is_none_without_a_session_name():
    assert settings.read_session_attach_target("/cockpit/jarvis-session/") is None
    assert settings.read_session_attach_target("/?sessionName=") is None


def test_build_attach_session_command_targets_the_default_socket_when_enumeration_is_empty():
    assert cockpit_tmux_commands.build_attach_session_command(
        TMUX_EXECUTABLE_PATH, "", "dotfiles"
    ) == [TMUX_EXECUTABLE_PATH, "attach-session", "-t", "dotfiles"]


def test_build_attach_session_command_uses_the_enumeration_socket_when_named():
    assert cockpit_tmux_commands.build_attach_session_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "reports-deploy"
    ) == [
        TMUX_EXECUTABLE_PATH,
        "-L",
        "cockpit",
        "attach-session",
        "-t",
        "reports-deploy",
    ]


def test_resolve_session_command_attaches_the_requested_session_on_the_enumeration_socket():
    resolved = server.resolve_session_command(
        _FakeWebsocketConnection("/cockpit/jarvis-session/?sessionName=dotfiles"),
        _attach_settings(),
    )
    assert resolved == [
        TMUX_EXECUTABLE_PATH,
        "attach-session",
        "-t",
        "dotfiles",
    ]


def test_resolve_session_command_attaches_the_requested_session_over_ssh_when_a_remote_host_is_set():
    remote_settings = dataclasses.replace(
        _attach_settings(), cockpit_tmux_remote_ssh_host="lucas.zanoni@kira"
    )
    resolved = server.resolve_session_command(
        _FakeWebsocketConnection("/cockpit/jarvis-session/?sessionName=dotfiles"),
        remote_settings,
    )
    assert resolved == [
        "ssh",
        "-tt",
        "lucas.zanoni@kira",
        f"{TMUX_EXECUTABLE_PATH} attach-session -t dotfiles",
    ]


def test_resolve_session_command_keeps_the_static_command_without_a_session_target():
    settings_with_static_command = _attach_settings()
    resolved = server.resolve_session_command(
        _FakeWebsocketConnection("/cockpit/jarvis-session/"),
        settings_with_static_command,
    )
    assert resolved == settings_with_static_command.session_command
