import cockpit_lifecycle_control
import pytest
from cockpit_multiplexer_test_doubles import (
    COCKPIT_SOCKET_PREFIX,
    RecordingSubprocessRunner,
)
from cockpit_multiplexer_test_doubles import (
    dispatch_through_tmux as dispatch,
)


def test_list_sessions_returns_the_serialized_inventory_as_plain_data():
    runner = RecordingSubprocessRunner(
        {
            "list-sessions": "jarvis-refactor\n",
            "list-windows": "jarvis-refactor\t@1\tclaude\tclaude\n",
        }
    )

    response = dispatch({"operation": "list-sessions"}, runner)

    assert response == {
        "operation": "list-sessions",
        "sessions": [
            {
                "sessionName": "jarvis-refactor",
                "windows": [
                    {
                        "windowIdentifier": "@1",
                        "windowTitle": "claude",
                        "agentDriver": "claude",
                        "terminalIdentifier": "",
                    }
                ],
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


def test_close_window_runs_the_kill_window_command():
    runner = RecordingSubprocessRunner()

    dispatch({"operation": "close-window", "windowIdentifier": "@7"}, runner)

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "kill-window", "-t", "@7"]
    ]


def test_an_unsupported_operation_is_rejected():
    runner = RecordingSubprocessRunner()

    with pytest.raises(cockpit_lifecycle_control.UnsupportedCockpitLifecycleOperation):
        dispatch({"operation": "detonate"}, runner)

    assert runner.executed_commands == []
