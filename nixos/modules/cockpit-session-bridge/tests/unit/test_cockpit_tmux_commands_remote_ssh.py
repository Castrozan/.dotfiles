import shlex
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_tmux_commands


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
WINDOW_INVENTORY_LIST_FORMAT = (
    "#{session_name}\t#{window_id}\t#{pane_current_command}\t#{window_name}"
)
REMOTE_SSH_HOST = "lucas.zanoni@kira"
SSH = ["ssh", *cockpit_tmux_commands.NON_INTERACTIVE_SSH_OPTIONS]
REMOTE_TMUX = cockpit_tmux_commands.REMOTE_TMUX_EXECUTABLE


def test_remote_ssh_invocation_uses_non_interactive_options():
    assert cockpit_tmux_commands.NON_INTERACTIVE_SSH_OPTIONS == [
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=10",
    ]


def test_remote_command_uses_a_bare_tmux_not_the_local_store_path():
    remote_list_sessions_command = cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, "", remote_ssh_host=REMOTE_SSH_HOST
    )
    assert remote_list_sessions_command[-1].startswith(f"{REMOTE_TMUX} ")
    assert "/nix/store/" not in remote_list_sessions_command[-1]
    assert TMUX_EXECUTABLE_PATH not in remote_list_sessions_command[-1]


def test_enumeration_builders_cross_ssh_as_one_shell_quoted_remote_command():
    assert cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, "", remote_ssh_host=REMOTE_SSH_HOST
    ) == [
        *SSH,
        REMOTE_SSH_HOST,
        f"{REMOTE_TMUX} list-sessions -F '#{{session_name}}'",
    ]
    assert cockpit_tmux_commands.build_list_windows_command(
        TMUX_EXECUTABLE_PATH, "", remote_ssh_host=REMOTE_SSH_HOST
    ) == [
        *SSH,
        REMOTE_SSH_HOST,
        shlex.join(
            [
                REMOTE_TMUX,
                "list-windows",
                "-a",
                "-F",
                WINDOW_INVENTORY_LIST_FORMAT,
            ]
        ),
    ]


def test_enumeration_format_argument_is_quoted_so_the_remote_shell_keeps_it():
    remote_list_sessions_command = cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, "", remote_ssh_host=REMOTE_SSH_HOST
    )
    assert "'#{session_name}'" in remote_list_sessions_command[-1]
    assert not remote_list_sessions_command[-1].endswith("-F")


def test_attach_builder_forces_a_remote_pseudoterminal_when_a_remote_host_is_given():
    assert cockpit_tmux_commands.build_attach_session_command(
        TMUX_EXECUTABLE_PATH, "", "todos", remote_ssh_host=REMOTE_SSH_HOST
    ) == [
        *SSH,
        "-tt",
        REMOTE_SSH_HOST,
        f"{REMOTE_TMUX} attach-session -t todos",
    ]


def test_remote_attach_target_with_shell_metacharacters_is_quoted_not_executed():
    assert cockpit_tmux_commands.build_attach_session_command(
        TMUX_EXECUTABLE_PATH, "", "feature; rm -rf /", remote_ssh_host=REMOTE_SSH_HOST
    ) == [
        *SSH,
        "-tt",
        REMOTE_SSH_HOST,
        f"{REMOTE_TMUX} attach-session -t " + shlex.quote("feature; rm -rf /"),
    ]


def test_remote_ssh_host_preserves_the_named_socket_flag_inside_the_ssh_command():
    assert cockpit_tmux_commands.build_list_sessions_command(
        TMUX_EXECUTABLE_PATH, "cockpit", remote_ssh_host=REMOTE_SSH_HOST
    ) == [
        *SSH,
        REMOTE_SSH_HOST,
        f"{REMOTE_TMUX} -L cockpit list-sessions -F '#{{session_name}}'",
    ]
