import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_tmux_commands


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
COCKPIT_SOCKET_PREFIX = [TMUX_EXECUTABLE_PATH, "-L", "cockpit"]
WINDOW_INVENTORY_LIST_FORMAT = (
    "#{session_name}\t#{window_id}\t#{pane_current_command}\t#{window_name}"
)


def test_list_and_mutation_builders_target_the_named_socket_when_one_is_given():
    socketed_commands = [
        cockpit_tmux_commands.build_list_sessions_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
        cockpit_tmux_commands.build_list_windows_command(
            TMUX_EXECUTABLE_PATH, "cockpit"
        ),
        cockpit_tmux_commands.build_open_session_command(
            TMUX_EXECUTABLE_PATH, "cockpit", "jarvis-refactor"
        ),
        cockpit_tmux_commands.build_close_session_command(
            TMUX_EXECUTABLE_PATH, "cockpit", "jarvis-refactor"
        ),
        cockpit_tmux_commands.build_close_window_command(
            TMUX_EXECUTABLE_PATH, "cockpit", "@7"
        ),
    ]
    for socketed_command in socketed_commands:
        assert socketed_command[:3] == COCKPIT_SOCKET_PREFIX


def test_list_builders_omit_the_socket_flag_when_the_enumeration_socket_is_empty():
    assert cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, ""
    ) == [TMUX_EXECUTABLE_PATH, "list-sessions", "-F", "#{session_name}"]
    assert cockpit_tmux_commands.build_list_windows_command(
        TMUX_EXECUTABLE_PATH, ""
    ) == [
        TMUX_EXECUTABLE_PATH,
        "list-windows",
        "-a",
        "-F",
        WINDOW_INVENTORY_LIST_FORMAT,
    ]


def test_build_list_sessions_command_requests_one_session_name_per_line():
    assert cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, "cockpit"
    ) == [*COCKPIT_SOCKET_PREFIX, "list-sessions", "-F", "#{session_name}"]


def test_build_list_windows_command_lists_every_window_across_all_sessions():
    assert cockpit_tmux_commands.build_list_windows_command(
        TMUX_EXECUTABLE_PATH, "cockpit"
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "list-windows",
        "-a",
        "-F",
        WINDOW_INVENTORY_LIST_FORMAT,
    ]


def test_build_open_session_command_starts_a_detached_named_session():
    assert cockpit_tmux_commands.build_open_session_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "reports-deploy"
    ) == [*COCKPIT_SOCKET_PREFIX, "new-session", "-d", "-s", "reports-deploy"]


def test_build_rename_session_command_targets_the_current_name():
    assert cockpit_tmux_commands.build_rename_session_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "reports-deploy", "reports-rollback"
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "rename-session",
        "-t",
        "reports-deploy",
        "reports-rollback",
    ]


def test_build_close_session_command_kills_the_named_session():
    assert cockpit_tmux_commands.build_close_session_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "reports-deploy"
    ) == [*COCKPIT_SOCKET_PREFIX, "kill-session", "-t", "reports-deploy"]


def test_build_open_window_runs_the_agent_launch_command_inside_the_new_window():
    assert cockpit_tmux_commands.build_open_window_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "jarvis-refactor", "claude", "exec claude"
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
    assert cockpit_tmux_commands.build_open_window_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "jarvis-refactor", "scratch", ""
    ) == [
        *COCKPIT_SOCKET_PREFIX,
        "new-window",
        "-t",
        "jarvis-refactor",
        "-n",
        "scratch",
    ]


def test_build_close_window_targets_the_window_identifier():
    assert cockpit_tmux_commands.build_close_window_command(
        TMUX_EXECUTABLE_PATH, "cockpit", "@7"
    ) == [*COCKPIT_SOCKET_PREFIX, "kill-window", "-t", "@7"]


def test_build_attach_session_command_attaches_locally_when_no_remote_host_is_given():
    assert cockpit_tmux_commands.build_attach_session_command(
        TMUX_EXECUTABLE_PATH, "", "todos"
    ) == [TMUX_EXECUTABLE_PATH, "-u", "attach-session", "-t", "todos"]
