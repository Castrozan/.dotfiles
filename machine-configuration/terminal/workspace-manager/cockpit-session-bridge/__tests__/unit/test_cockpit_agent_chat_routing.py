import asyncio
import json

from cockpit_agent_chat_test_doubles import (
    OPENCLAW_STYLE_COMMAND,
    RecordingAgentCommandRunner,
    build_agent_chat_settings,
    run_agent_chat,
)
from cockpit_lifecycle_websocket_test_doubles import ScriptedLifecycleControlWebsocket

import cockpit_agent_chat
import server
import settings


def test_an_unconfigured_agent_command_never_runs_anything():
    runner = RecordingAgentCommandRunner()

    websocket_connection = run_agent_chat(['{"text":"hello"}'], [], runner)

    assert runner.executed_commands == []
    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "error",
        "text": "no agent chat command is configured",
    }


def test_a_disallowed_origin_on_the_agent_chat_path_never_runs_the_agent():
    runner = RecordingAgentCommandRunner()

    websocket_connection = run_agent_chat(
        ['{"text":"hello"}'],
        OPENCLAW_STYLE_COMMAND,
        runner,
        request_origin="https://evil.test",
    )

    assert runner.executed_commands == []
    assert websocket_connection.close_calls[0][0] == 1008
    assert websocket_connection.sent_messages == []


def test_the_agent_chat_path_routes_away_from_the_pseudoterminal_session():
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"text":"hello"}'],
        request_path=cockpit_agent_chat.COCKPIT_AGENT_CHAT_PATH,
    )

    asyncio.run(
        server.handle_bridge_websocket_connection(
            websocket_connection,
            build_agent_chat_settings([]),
            None,
        )
    )

    assert json.loads(websocket_connection.sent_messages[0]) == {
        "type": "error",
        "text": "no agent chat command is configured",
    }


def test_the_agent_chat_command_is_read_from_the_environment_as_json():
    resolved_settings = settings.resolve_bridge_settings(
        {
            "COCKPIT_SESSION_BRIDGE_AGENT_CHAT_COMMAND_JSON": json.dumps(
                OPENCLAW_STYLE_COMMAND
            )
        }
    )

    assert resolved_settings.agent_chat_command == OPENCLAW_STYLE_COMMAND


def test_an_absent_agent_chat_command_leaves_the_route_unconfigured():
    assert settings.resolve_bridge_settings({}).agent_chat_command == []
