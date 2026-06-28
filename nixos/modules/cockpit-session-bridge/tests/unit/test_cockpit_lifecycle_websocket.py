import asyncio
import json

from cockpit_lifecycle_websocket_test_doubles import (
    COCKPIT_SOCKET_PREFIX,
    TMUX_EXECUTABLE_PATH,
    RecordingSubprocessRunner,
    ScriptedLifecycleControlWebsocket,
)

import cockpit_lifecycle_control
import cockpit_lifecycle_websocket


def drive_lifecycle_control(websocket_connection, subprocess_runner):
    asyncio.run(
        cockpit_lifecycle_websocket.stream_cockpit_lifecycle_control_over_websocket(
            websocket_connection,
            TMUX_EXECUTABLE_PATH,
            cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
            subprocess_runner=subprocess_runner,
        )
    )


def decoded_replies(websocket_connection):
    return [json.loads(message) for message in websocket_connection.sent_messages]


def test_a_list_sessions_request_replies_with_the_serialized_inventory():
    runner = RecordingSubprocessRunner(
        {
            "list-sessions": "reports-deploy\n",
            "list-windows": "reports-deploy\t@1\tclaude\tclaude\n",
        }
    )
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"operation":"list-sessions"}']
    )

    drive_lifecycle_control(websocket_connection, runner)

    assert decoded_replies(websocket_connection) == [
        {
            "operation": "list-sessions",
            "sessions": [
                {
                    "sessionName": "reports-deploy",
                    "windows": [
                        {
                            "windowIdentifier": "@1",
                            "windowTitle": "claude",
                            "agentDriver": "claude",
                        }
                    ],
                }
            ],
        }
    ]


def test_a_mutation_request_runs_the_command_and_replies_with_the_outcome():
    runner = RecordingSubprocessRunner()
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"operation":"open-session","sessionName":"reports-deploy"}']
    )

    drive_lifecycle_control(websocket_connection, runner)

    assert runner.executed_commands == [
        [*COCKPIT_SOCKET_PREFIX, "new-session", "-d", "-s", "reports-deploy"]
    ]
    assert decoded_replies(websocket_connection) == [
        {"operation": "open-session", "exitCode": 0, "standardError": ""}
    ]


def test_an_invalid_json_request_replies_with_an_error_and_never_runs_tmux():
    runner = RecordingSubprocessRunner()
    websocket_connection = ScriptedLifecycleControlWebsocket(["not-json-at-all"])

    drive_lifecycle_control(websocket_connection, runner)

    assert runner.executed_commands == []
    assert decoded_replies(websocket_connection) == [{"error": "invalid-request"}]


def test_an_unsupported_operation_replies_with_an_error_and_never_runs_tmux():
    runner = RecordingSubprocessRunner()
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"operation":"detonate"}']
    )

    drive_lifecycle_control(websocket_connection, runner)

    assert runner.executed_commands == []
    assert decoded_replies(websocket_connection) == [
        {"error": "unsupported-operation", "operation": "detonate"}
    ]


def test_a_valid_operation_missing_a_required_field_replies_with_an_error_and_never_runs_tmux():
    runner = RecordingSubprocessRunner()
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"operation":"open-session"}']
    )

    drive_lifecycle_control(websocket_connection, runner)

    assert runner.executed_commands == []
    assert decoded_replies(websocket_connection) == [{"error": "invalid-request"}]


def test_each_request_on_one_connection_gets_its_own_reply_in_order():
    runner = RecordingSubprocessRunner({"list-sessions": "", "list-windows": ""})
    websocket_connection = ScriptedLifecycleControlWebsocket(
        [
            '{"operation":"open-session","sessionName":"build"}',
            '{"operation":"list-sessions"}',
        ]
    )

    drive_lifecycle_control(websocket_connection, runner)

    assert decoded_replies(websocket_connection) == [
        {"operation": "open-session", "exitCode": 0, "standardError": ""},
        {"operation": "list-sessions", "sessions": []},
    ]
