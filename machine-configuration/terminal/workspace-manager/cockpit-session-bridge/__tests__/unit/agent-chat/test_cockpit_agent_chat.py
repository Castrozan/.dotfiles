import asyncio
import json

from cockpit_agent_chat_test_doubles import (
    OPENCLAW_STYLE_COMMAND,
    RecordingAgentCommandRunner,
    ScriptedAgentProcess,
    run_agent_chat,
)

import cockpit_agent_chat


def test_the_owner_message_is_substituted_into_the_configured_agent_command():
    runner = RecordingAgentCommandRunner()

    run_agent_chat(
        ['{"text":"status report","sessionKey":"global"}'],
        OPENCLAW_STYLE_COMMAND,
        runner,
    )

    assert runner.executed_commands == [
        ["agent-cli", "--message", "status report", "--session-key", "global", "--json"]
    ]


def test_the_agent_reply_text_is_returned_to_the_owner():
    runner = RecordingAgentCommandRunner()

    websocket_connection = run_agent_chat(
        ['{"text":"status report"}'], OPENCLAW_STYLE_COMMAND, runner
    )

    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "reply",
        "text": "on it",
    }


def test_a_missing_session_key_falls_back_to_the_default_session():
    runner = RecordingAgentCommandRunner()

    run_agent_chat(['{"text":"hello"}'], OPENCLAW_STYLE_COMMAND, runner)

    assert runner.executed_commands[0][4] == cockpit_agent_chat.DEFAULT_SESSION_KEY


def test_plain_text_agent_output_is_returned_unchanged():
    runner = RecordingAgentCommandRunner(ScriptedAgentProcess(b"  plain answer  \n"))

    websocket_connection = run_agent_chat(
        ['{"text":"hello"}'], OPENCLAW_STYLE_COMMAND, runner
    )

    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "reply",
        "text": "plain answer",
    }


def test_a_failing_agent_command_reports_its_error_instead_of_a_reply():
    runner = RecordingAgentCommandRunner(
        ScriptedAgentProcess(b"", b"gateway refused the connection", returncode=1)
    )

    websocket_connection = run_agent_chat(
        ['{"text":"hello"}'], OPENCLAW_STYLE_COMMAND, runner
    )

    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "error",
        "text": "gateway refused the connection",
    }


def test_an_empty_message_is_rejected_without_running_the_agent():
    runner = RecordingAgentCommandRunner()

    websocket_connection = run_agent_chat(
        ['{"text":"   "}'], OPENCLAW_STYLE_COMMAND, runner
    )

    assert runner.executed_commands == []
    assert json.loads(websocket_connection.sent_messages[0])["type"] == "error"


def test_the_agent_command_is_run_with_both_streams_captured():
    runner = RecordingAgentCommandRunner()

    run_agent_chat(['{"text":"status report"}'], OPENCLAW_STYLE_COMMAND, runner)

    assert runner.executed_keyword_arguments == [
        {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
        }
    ]


def test_an_uncaptured_stream_answers_with_an_error_instead_of_crashing():
    runner = RecordingAgentCommandRunner(
        ScriptedAgentProcess(standard_output=None, standard_error=None, returncode=1)
    )

    websocket_connection = run_agent_chat(
        ['{"text":"status report"}'], OPENCLAW_STYLE_COMMAND, runner
    )

    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "error",
        "text": "the agent command failed",
    }
