import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
from cockpit_multiplexer_test_doubles import (
    COCKPIT_SOCKET_PREFIX,
    TMUX_EXECUTABLE_PATH,
    RecordingSubprocessRunner,
    dispatch_through_tmux as dispatch,
)


def test_close_operations_target_the_mutation_socket_even_when_enumeration_reads_the_default_socket():
    owner_default_enumeration_policy = (
        cockpit_lifecycle_control.CockpitTmuxSocketPolicy(
            enumeration_socket_name="", mutation_socket_name="cockpit"
        )
    )

    close_session_runner = RecordingSubprocessRunner()
    dispatch(
        {"operation": "close-session", "sessionName": "owner-real-work"},
        close_session_runner,
        owner_default_enumeration_policy,
    )

    close_window_runner = RecordingSubprocessRunner()
    dispatch(
        {"operation": "close-window", "windowIdentifier": "@1"},
        close_window_runner,
        owner_default_enumeration_policy,
    )

    assert close_session_runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-session", "-t", "owner-real-work"]
    ]
    assert close_window_runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-window", "-t", "@1"]
    ]
    assert close_session_runner.executed_commands[0][1:3] == ["-L", "cockpit"]
    assert close_window_runner.executed_commands[0][1:3] == ["-L", "cockpit"]


def test_remote_ssh_host_forwards_enumeration_over_ssh_while_mutations_stay_local():
    remote_enumeration_policy = cockpit_lifecycle_control.CockpitTmuxSocketPolicy(
        enumeration_socket_name="",
        mutation_socket_name="cockpit",
        remote_ssh_host="lucas.zanoni@kira",
    )

    list_sessions_runner = RecordingSubprocessRunner()
    dispatch(
        {"operation": "list-sessions"},
        list_sessions_runner,
        remote_enumeration_policy,
    )

    close_session_runner = RecordingSubprocessRunner()
    dispatch(
        {"operation": "close-session", "sessionName": "owner-real-work"},
        close_session_runner,
        remote_enumeration_policy,
    )

    assert list_sessions_runner.executed_commands
    for executed_command in list_sessions_runner.executed_commands:
        assert executed_command[0] == "ssh"
        assert "lucas.zanoni@kira" in executed_command
        assert executed_command[-1].startswith("tmux ")
        assert "/nix/store/" not in executed_command[-1]
    assert close_session_runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-session", "-t", "owner-real-work"]
    ]
    assert "ssh" not in close_session_runner.executed_commands[0]


def test_list_sessions_reads_the_default_socket_when_enumeration_is_empty_while_mutations_stay_sandboxed():
    owner_default_enumeration_policy = (
        cockpit_lifecycle_control.CockpitTmuxSocketPolicy(
            enumeration_socket_name="", mutation_socket_name="cockpit"
        )
    )
    list_sessions_runner = RecordingSubprocessRunner(
        {
            "list-sessions": "dotfiles\n",
            "list-windows": "dotfiles\t@216\tclaude\tclaude\n",
        }
    )

    dispatch(
        {"operation": "list-sessions"},
        list_sessions_runner,
        owner_default_enumeration_policy,
    )

    assert list_sessions_runner.executed_commands
    for executed_command in list_sessions_runner.executed_commands:
        assert "-L" not in executed_command
        assert executed_command[0] == TMUX_EXECUTABLE_PATH
        assert executed_command[1].startswith("list-")


def test_list_sessions_detects_the_agent_driver_from_the_pane_current_command():
    claude_runner = RecordingSubprocessRunner(
        {
            "list-sessions": "dotfiles\n",
            "list-windows": "dotfiles\t@216\tclaude\tclaude\n",
        }
    )
    claude_response = dispatch(
        {"operation": "list-sessions"},
        claude_runner,
        cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
    )
    assert claude_response["sessions"][0]["windows"][0]["agentDriver"] == "claude"

    plain_command_runner = RecordingSubprocessRunner(
        {
            "list-sessions": "dotfiles\n",
            "list-windows": "dotfiles\t@216\tpython3.12\teditor\n",
        }
    )
    plain_command_response = dispatch(
        {"operation": "list-sessions"},
        plain_command_runner,
        cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
    )
    assert plain_command_response["sessions"][0]["windows"][0]["agentDriver"] is None
