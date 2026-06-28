import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_tmux_lifecycle


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"


def test_parse_inventory_groups_windows_under_their_session_in_listing_order():
    parsed_sessions = cockpit_tmux_lifecycle.parse_cockpit_session_inventory(
        "jarvis-refactor\nreports-deploy\n",
        "jarvis-refactor\t@1\tclaude\tagent\n"
        "jarvis-refactor\t@2\tcodex\tassistant\n"
        "reports-deploy\t@3\tclaude\tdeploy\n",
    )
    assert parsed_sessions == [
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="jarvis-refactor",
            windows=(
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@1", "agent", "claude"),
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@2", "assistant", "codex"),
            ),
        ),
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="reports-deploy",
            windows=(
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@3", "deploy", "claude"),
            ),
        ),
    ]


def test_parse_inventory_returns_no_sessions_for_empty_tmux_output():
    assert cockpit_tmux_lifecycle.parse_cockpit_session_inventory("", "") == []


def test_parse_inventory_keeps_a_session_that_has_no_listed_windows():
    parsed_sessions = cockpit_tmux_lifecycle.parse_cockpit_session_inventory(
        "empty-domain\n", ""
    )
    assert parsed_sessions == [
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="empty-domain", windows=()
        )
    ]


def test_parse_inventory_preserves_a_window_title_that_contains_the_separator():
    parsed_sessions = cockpit_tmux_lifecycle.parse_cockpit_session_inventory(
        "domain\n", "domain\t@9\tclaude\treview\tstage\n"
    )
    assert parsed_sessions[0].windows[0] == cockpit_tmux_lifecycle.CockpitTmuxWindow(
        "@9", "review\tstage", "claude"
    )


def test_list_cockpit_sessions_runs_both_listings_and_returns_the_parsed_inventory():
    executed_commands = []

    async def fake_subprocess_runner(tmux_command):
        executed_commands.append(tmux_command)
        if "list-sessions" in tmux_command:
            return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(0, "domain\n", "")
        return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(
            0, "domain\t@1\tclaude\tagent\n", ""
        )

    parsed_sessions = asyncio.run(
        cockpit_tmux_lifecycle.list_cockpit_sessions(
            TMUX_EXECUTABLE_PATH, "cockpit", subprocess_runner=fake_subprocess_runner
        )
    )

    assert parsed_sessions == [
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="domain",
            windows=(
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@1", "agent", "claude"),
            ),
        )
    ]
    assert executed_commands == [
        cockpit_tmux_lifecycle.build_list_sessions_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
        cockpit_tmux_lifecycle.build_list_windows_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
    ]
