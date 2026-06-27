import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "jarvis_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
import cockpit_tmux_lifecycle
import pytest


TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
COCKPIT_SOCKET_PREFIX = [TMUX_EXECUTABLE_PATH, "-L", "cockpit"]


class RecordingSubprocessRunner:
    def __init__(self, scripted_outputs=None):
        self.executed_commands = []
        self._scripted_outputs = scripted_outputs or {}

    async def __call__(self, tmux_command):
        self.executed_commands.append(tmux_command)
        for command_marker, output in self._scripted_outputs.items():
            if command_marker in tmux_command:
                return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(0, output, "")
        return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(0, "", "")


def dispatch(lifecycle_request, subprocess_runner):
    return asyncio.run(
        cockpit_lifecycle_control.dispatch_cockpit_lifecycle_request(
            TMUX_EXECUTABLE_PATH, lifecycle_request, subprocess_runner=subprocess_runner
        )
    )


def test_list_sessions_returns_the_serialized_inventory_as_plain_data():
    runner = RecordingSubprocessRunner(
        {
            "list-sessions": "jarvis-refactor\n",
            "list-windows": "jarvis-refactor\t@1\tclaude\n",
        }
    )

    response = dispatch({"operation": "list-sessions"}, runner)

    assert response == {
        "operation": "list-sessions",
        "sessions": [
            {
                "sessionName": "jarvis-refactor",
                "windows": [{"windowIdentifier": "@1", "windowTitle": "claude"}],
            }
        ],
    }


def test_open_session_runs_the_detached_new_session_command():
    runner = RecordingSubprocessRunner()

    response = dispatch(
        {"operation": "open-session", "sessionName": "reports-deploy"}, runner
    )

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "new-session", "-d", "-s", "reports-deploy"]
    ]
    assert response == {
        "operation": "open-session",
        "exitCode": 0,
        "standardError": "",
    }


def test_rename_session_threads_both_names_into_the_command():
    runner = RecordingSubprocessRunner()

    dispatch(
        {
            "operation": "rename-session",
            "currentSessionName": "reports-deploy",
            "newSessionName": "reports-rollback",
        },
        runner,
    )

    assert runner.executed_commands == [
        [
            *COCKPIT_SOCKET_PREFIX,
            "rename-session",
            "-t",
            "reports-deploy",
            "reports-rollback",
        ]
    ]


def test_close_session_runs_the_kill_session_command():
    runner = RecordingSubprocessRunner()

    dispatch({"operation": "close-session", "sessionName": "reports-deploy"}, runner)

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-session", "-t", "reports-deploy"]
    ]


def test_open_window_threads_the_agent_launch_command():
    runner = RecordingSubprocessRunner()

    dispatch(
        {
            "operation": "open-window",
            "sessionName": "jarvis-refactor",
            "windowTitle": "codex",
            "agentLaunchCommand": "exec codex",
        },
        runner,
    )

    assert runner.executed_commands == [
        [
            *COCKPIT_SOCKET_PREFIX,
            "new-window",
            "-t",
            "jarvis-refactor",
            "-n",
            "codex",
            "exec codex",
        ]
    ]


def test_open_window_without_an_agent_launch_command_opens_an_empty_window():
    runner = RecordingSubprocessRunner()

    dispatch(
        {
            "operation": "open-window",
            "sessionName": "jarvis-refactor",
            "windowTitle": "scratch",
        },
        runner,
    )

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "new-window", "-t", "jarvis-refactor", "-n", "scratch"]
    ]


def test_close_window_runs_the_kill_window_command():
    runner = RecordingSubprocessRunner()

    dispatch({"operation": "close-window", "windowIdentifier": "@7"}, runner)

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-window", "-t", "@7"]
    ]


def test_a_failed_mutation_surfaces_the_exit_code_and_standard_error():
    async def failing_runner(tmux_command):
        return cockpit_tmux_lifecycle.CockpitTmuxCommandResult(
            1, "", "duplicate session: reports-deploy\n"
        )

    response = dispatch(
        {"operation": "open-session", "sessionName": "reports-deploy"}, failing_runner
    )

    assert response == {
        "operation": "open-session",
        "exitCode": 1,
        "standardError": "duplicate session: reports-deploy\n",
    }


def test_an_unsupported_operation_is_rejected():
    runner = RecordingSubprocessRunner()

    with pytest.raises(cockpit_lifecycle_control.UnsupportedCockpitLifecycleOperation):
        dispatch({"operation": "detonate"}, runner)

    assert runner.executed_commands == []
