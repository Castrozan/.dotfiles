import asyncio
import json

from cockpit_lifecycle_websocket_test_doubles import ScriptedLifecycleControlWebsocket

import cockpit_agent_chat
import server
import settings

OPENCLAW_STYLE_COMMAND = [
    "agent-cli",
    "--message",
    cockpit_agent_chat.MESSAGE_PLACEHOLDER,
    "--session-key",
    cockpit_agent_chat.SESSION_KEY_PLACEHOLDER,
    "--json",
]


class ScriptedAgentProcess:
    def __init__(self, standard_output, standard_error=b"", returncode=0):
        self._standard_output = standard_output
        self._standard_error = standard_error
        self.returncode = returncode

    async def communicate(self):
        return self._standard_output, self._standard_error


class RecordingAgentCommandRunner:
    def __init__(self, agent_process=None):
        self.executed_commands = []
        self.executed_keyword_arguments = []
        self._agent_process = agent_process or ScriptedAgentProcess(
            json.dumps({"text": "on it"}).encode()
        )

    async def __call__(self, *command_arguments, **keyword_arguments):
        self.executed_commands.append(list(command_arguments))
        self.executed_keyword_arguments.append(keyword_arguments)
        return self._agent_process


def build_agent_chat_settings(agent_chat_command):
    return settings.CockpitSessionBridgeSettings(
        listen_address="127.0.0.1",
        listen_port=8787,
        session_command=["/bin/sh", "-il"],
        allowed_request_origin="https://lucaszanoni.com",
        terminal_type="xterm-256color",
        agent_chat_command=agent_chat_command,
    )


def run_agent_chat(request_messages, agent_chat_command, runner, request_origin=None):
    websocket_connection = ScriptedLifecycleControlWebsocket(
        request_messages,
        request_path=cockpit_agent_chat.COCKPIT_AGENT_CHAT_PATH,
        **({"request_origin": request_origin} if request_origin else {}),
    )
    asyncio.run(
        server.bridge_agent_chat_over_websocket(
            websocket_connection,
            build_agent_chat_settings(agent_chat_command),
            subprocess_runner=runner,
        )
    )
    return websocket_connection
