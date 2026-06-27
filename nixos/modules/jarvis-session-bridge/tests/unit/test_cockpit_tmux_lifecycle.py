import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "jarvis_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_tmux_lifecycle


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
COCKPIT_SOCKET_PREFIX = [TMUX_EXECUTABLE_PATH, "-L", "cockpit"]


def test_every_lifecycle_command_targets_the_dedicated_cockpit_socket_not_jarvis():
    built_commands = [
        cockpit_tmux_lifecycle.build_list_sessions_command(TMUX_EXECUTABLE_PATH),
        cockpit_tmux_lifecycle.build_list_windows_command(TMUX_EXECUTABLE_PATH),
        cockpit_tmux_lifecycle.build_open_session_command(
            TMUX_EXECUTABLE_PATH, "jarvis-refactor"
        ),
        cockpit_tmux_lifecycle.build_close_session_command(
            TMUX_EXECUTABLE_PATH, "jarvis-refactor"
        ),
    ]
    for built_command in built_commands:
        assert built_command[:3] == COCKPIT_SOCKET_PREFIX


def test_build_list_sessions_command_requests_one_session_name_per_line():
    assert cockpit_tmux_lifecycle.build_list_sessions_command(TMUX_EXECUTABLE_PATH) == [
        *COCKPIT_SOCKET_PREFIX,
        "list-sessions",
        "-F",
        "#{session_name}",
    ]


def test_build_list_windows_command_lists_every_window_across_all_sessions():
    assert cockpit_tmux_lifecycle.build_list_windows_command(TMUX_EXECUTABLE_PATH) == [
        *COCKPIT_SOCKET_PREFIX,
        "list-windows",
        "-a",
        "-F",
        "#{session_name}\t#{window_id}\t#{window_name}",
    ]


def test_build_open_session_command_starts_a_detached_named_session():
    assert cockpit_tmux_lifecycle.build_open_session_command(
        TMUX_EXECUTABLE_PATH, "reports-deploy"
    ) == [*COCKPIT_SOCKET_PREFIX, "new-session", "-d", "-s", "reports-deploy"]


def test_build_rename_session_command_targets_the_current_name():
    assert cockpit_tmux_lifecycle.build_rename_session_command(
        TMUX_EXECUTABLE_PATH, "reports-deploy", "reports-rollback"
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "rename-session",
        "-t",
        "reports-deploy",
        "reports-rollback",
    ]


def test_build_close_session_command_kills_the_named_session():
    assert cockpit_tmux_lifecycle.build_close_session_command(
        TMUX_EXECUTABLE_PATH, "reports-deploy"
    ) == [*COCKPIT_SOCKET_PREFIX, "kill-session", "-t", "reports-deploy"]


def test_build_open_window_runs_the_agent_launch_command_inside_the_new_window():
    assert cockpit_tmux_lifecycle.build_open_window_command(
        TMUX_EXECUTABLE_PATH,
        "jarvis-refactor",
        "claude",
        "exec claude",
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "new-window",
        "-t",
        "jarvis-refactor",
        "-n",
        "claude",
        "exec claude",
    ]


def test_build_open_window_without_an_agent_launch_command_opens_an_empty_window():
    assert cockpit_tmux_lifecycle.build_open_window_command(
        TMUX_EXECUTABLE_PATH, "jarvis-refactor", "scratch", ""
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "new-window",
        "-t",
        "jarvis-refactor",
        "-n",
        "scratch",
    ]


def test_build_close_window_targets_the_window_identifier():
    assert cockpit_tmux_lifecycle.build_close_window_command(
        TMUX_EXECUTABLE_PATH, "@7"
    ) == [*COCKPIT_SOCKET_PREFIX, "kill-window", "-t", "@7"]


def test_parse_inventory_groups_windows_under_their_session_in_listing_order():
    parsed_sessions = cockpit_tmux_lifecycle.parse_cockpit_session_inventory(
        "jarvis-refactor\nreports-deploy\n",
        "jarvis-refactor\t@1\tclaude\n"
        "jarvis-refactor\t@2\tcodex\n"
        "reports-deploy\t@3\tclaude\n",
    )
    assert parsed_sessions == [
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="jarvis-refactor",
            windows=(
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@1", "claude"),
                cockpit_tmux_lifecycle.CockpitTmuxWindow("@2", "codex"),
            ),
        ),
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="reports-deploy",
            windows=(cockpit_tmux_lifecycle.CockpitTmuxWindow("@3", "claude"),),
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
        "domain\n", "domain\t@9\tclaude\treview\n"
    )
    assert parsed_sessions[0].windows[0] == cockpit_tmux_lifecycle.CockpitTmuxWindow(
        "@9", "claude\treview"
    )


def test_list_cockpit_sessions_runs_both_listings_and_returns_the_parsed_inventory():
    executed_commands = []

    async def fake_subprocess_runner(tmux_command):
        executed_commands.append(tmux_command)
        if "list-sessions" in tmux_command:
            return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(0, "domain\n", "")
        return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(
            0, "domain\t@1\tclaude\n", ""
        )

    parsed_sessions = asyncio.run(
        cockpit_tmux_lifecycle.list_cockpit_sessions(
            TMUX_EXECUTABLE_PATH, subprocess_runner=fake_subprocess_runner
        )
    )

    assert parsed_sessions == [
        cockpit_tmux_lifecycle.CockpitTmuxSession(
            session_name="domain",
            windows=(cockpit_tmux_lifecycle.CockpitTmuxWindow("@1", "claude"),),
        )
    ]
    assert executed_commands == [
        cockpit_tmux_lifecycle.build_list_sessions_command(TMUX_EXECUTABLE_PATH),
        cockpit_tmux_lifecycle.build_list_windows_command(TMUX_EXECUTABLE_PATH),
    ]
