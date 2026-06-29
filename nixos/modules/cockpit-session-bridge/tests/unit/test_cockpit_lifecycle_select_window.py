import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
import cockpit_tmux_lifecycle


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
COCKPIT_SOCKET_PREFIX = [TMUX_EXECUTABLE_PATH, "-L", "cockpit"]


class RecordingSubprocessRunner:
    def __init__(self):
        self.executed_commands = []

    async def __call__(self, tmux_command):
        self.executed_commands.append(tmux_command)
        return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(0, "", "")


def dispatch(lifecycle_request, subprocess_runner, socket_policy=None):
    return asyncio.run(
        cockpit_lifecycle_control.dispatch_cockpit_lifecycle_request(
            TMUX_EXECUTABLE_PATH,
            socket_policy or cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
            lifecycle_request,
            subprocess_runner=subprocess_runner,
        )
    )


def test_select_window_runs_on_the_enumeration_socket_and_follows_the_client():
    runner = RecordingSubprocessRunner()

    response = dispatch(
        {"operation": "select-window", "windowIdentifier": "@7"}, runner
    )

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "select-window", "-t", "@7"]
    ]
    assert response == {
        "operation": "select-window",
        "exitCode": 0,
        "standardError": "",
    }


def test_select_window_targets_the_enumeration_socket_not_the_mutation_socket():
    runner = RecordingSubprocessRunner()
    split_socket_policy = cockpit_lifecycle_control.CockpitTmuxSocketPolicy(
        enumeration_socket_name="cockpit-enum",
        mutation_socket_name="cockpit-mut",
    )

    dispatch(
        {"operation": "select-window", "windowIdentifier": "@7"},
        runner,
        socket_policy=split_socket_policy,
    )

    assert runner.executed_commands == [
        [TMUX_EXECUTABLE_PATH, "-L", "cockpit-enum", "select-window", "-t", "@7"]
    ]


def test_select_window_forwards_to_the_remote_host_when_one_is_configured():
    runner = RecordingSubprocessRunner()
    remote_socket_policy = cockpit_lifecycle_control.CockpitTmuxSocketPolicy(
        remote_ssh_host="lucas.zanoni@kira",
    )

    dispatch(
        {"operation": "select-window", "windowIdentifier": "@7"},
        runner,
        socket_policy=remote_socket_policy,
    )

    executed_command = runner.executed_commands[0]
    assert executed_command[0] == "ssh"
    assert executed_command[-2] == "lucas.zanoni@kira"
    assert executed_command[-1] == "tmux -L cockpit select-window -t @7"
    assert "-tt" not in executed_command
