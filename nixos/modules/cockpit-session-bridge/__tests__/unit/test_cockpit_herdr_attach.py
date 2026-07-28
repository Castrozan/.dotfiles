import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

from cockpit_herdr_test_doubles import (
    HERDR_EXECUTABLE_PATH,
    ScriptedHerdrSubprocessRunner,
    build_herdr_multiplexer,
)


def build_attach_command(attach_target, remote_ssh_host=""):
    return asyncio.run(
        build_herdr_multiplexer(
            ScriptedHerdrSubprocessRunner(), remote_ssh_host
        ).build_attach_command(attach_target)
    )


def test_attaching_never_focuses_a_workspace_for_the_clients_already_connected():
    assert build_attach_command("dotfiles") == [
        HERDR_EXECUTABLE_PATH,
        "session",
        "attach",
        "default",
    ]


def test_attaching_an_unknown_workspace_still_attaches_the_session():
    assert build_attach_command("never-existed") == [
        HERDR_EXECUTABLE_PATH,
        "session",
        "attach",
        "default",
    ]


def test_a_remote_attach_allocates_a_pseudoterminal_and_calls_herdr_off_the_remote_path():
    attach_command = build_attach_command("dotfiles", "lucas.zanoni@kira")

    assert attach_command[0] == "ssh"
    assert "-tt" in attach_command
    assert attach_command[-2] == "lucas.zanoni@kira"
    assert HERDR_EXECUTABLE_PATH not in attach_command[-1]
    assert "focus" not in attach_command[-1]
    assert attach_command[-1] == "herdr session attach default"
