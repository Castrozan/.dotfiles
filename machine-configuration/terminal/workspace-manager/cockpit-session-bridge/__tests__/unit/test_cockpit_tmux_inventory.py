import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
import cockpit_multiplexer_port
import cockpit_tmux_commands
import cockpit_tmux_multiplexer


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"


def test_parse_inventory_groups_windows_under_their_session_in_listing_order():
    parsed_sessions = cockpit_tmux_multiplexer.parse_tmux_session_inventory(
        "jarvis-refactor\nreports-deploy\n",
        "jarvis-refactor\t@1\tclaude\tagent\n"
        "jarvis-refactor\t@2\tcodex\tassistant\n"
        "reports-deploy\t@3\tclaude\tdeploy\n",
    )
    assert parsed_sessions == [
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="jarvis-refactor",
            windows=(
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "@1", "agent", "claude"
                ),
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "@2", "assistant", "codex"
                ),
            ),
        ),
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="reports-deploy",
            windows=(
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "@3", "deploy", "claude"
                ),
            ),
        ),
    ]


def test_parse_inventory_returns_no_sessions_for_empty_tmux_output():
    assert cockpit_tmux_multiplexer.parse_tmux_session_inventory("", "") == []


def test_parse_inventory_keeps_a_session_that_has_no_listed_windows():
    parsed_sessions = cockpit_tmux_multiplexer.parse_tmux_session_inventory(
        "empty-domain\n", ""
    )
    assert parsed_sessions == [
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="empty-domain", windows=()
        )
    ]


def test_parse_inventory_preserves_a_window_title_that_contains_the_separator():
    parsed_sessions = cockpit_tmux_multiplexer.parse_tmux_session_inventory(
        "domain\n", "domain\t@9\tclaude\treview\tstage\n"
    )
    assert parsed_sessions[0].windows[
        0
    ] == cockpit_multiplexer_port.CockpitMultiplexerWindow(
        "@9", "review\tstage", "claude"
    )


def test_parse_inventory_leaves_a_plain_shell_window_without_an_agent_driver():
    parsed_sessions = cockpit_tmux_multiplexer.parse_tmux_session_inventory(
        "domain\n", "domain\t@4\tbash\tscratch\n"
    )
    assert parsed_sessions[0].windows[0].agent_driver == ""


def test_list_sessions_runs_both_listings_and_returns_the_parsed_inventory():
    executed_commands = []

    async def fake_subprocess_runner(tmux_command):
        executed_commands.append(tmux_command)
        if "list-sessions" in tmux_command:
            return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
                0, "domain\n", ""
            )
        return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
            0, "domain\t@1\tclaude\tagent\n", ""
        )

    multiplexer = cockpit_tmux_multiplexer.CockpitTmuxMultiplexer(
        TMUX_EXECUTABLE_PATH,
        cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
        subprocess_runner=fake_subprocess_runner,
    )
    parsed_sessions = asyncio.run(multiplexer.list_sessions())

    assert parsed_sessions == [
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="domain",
            windows=(
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "@1", "agent", "claude"
                ),
            ),
        )
    ]
    assert executed_commands == [
        cockpit_tmux_commands.build_list_sessions_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
        cockpit_tmux_commands.build_list_windows_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
    ]
