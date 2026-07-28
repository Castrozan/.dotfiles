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

DOTFILES_AIDP_TERMINAL_IDENTIFIER = "term_6569e1e60304f89"


def build_attach_command(attach_target, remote_ssh_host=""):
    return asyncio.run(
        build_herdr_multiplexer(
            ScriptedHerdrSubprocessRunner(), remote_ssh_host
        ).build_attach_command(attach_target)
    )


def test_attaching_drives_one_terminal_instead_of_the_whole_application():
    assert build_attach_command(DOTFILES_AIDP_TERMINAL_IDENTIFIER) == [
        HERDR_EXECUTABLE_PATH,
        "terminal",
        "attach",
        DOTFILES_AIDP_TERMINAL_IDENTIFIER,
    ]


def test_a_target_that_is_not_a_terminal_identifier_is_refused_before_it_builds_a_command():
    for rejected_target in ("", "dotfiles", "w1T:tB", "term_abc; rm -rf /", "term_"):
        try:
            build_attach_command(rejected_target)
        except ValueError:
            continue
        raise AssertionError(f"{rejected_target!r} should not build an attach command")


def test_a_remote_attach_allocates_a_pseudoterminal_and_calls_herdr_off_the_remote_path():
    attach_command = build_attach_command(
        DOTFILES_AIDP_TERMINAL_IDENTIFIER, "lucas.zanoni@kira"
    )

    assert attach_command[0] == "ssh"
    assert "-tt" in attach_command
    assert attach_command[-2] == "lucas.zanoni@kira"
    assert HERDR_EXECUTABLE_PATH not in attach_command[-1]
    assert "focus" not in attach_command[-1]
    assert (
        attach_command[-1]
        == f"herdr terminal attach {DOTFILES_AIDP_TERMINAL_IDENTIFIER}"
    )
