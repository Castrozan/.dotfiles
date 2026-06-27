import types

import jarvis_session_bridge_runtime_test_doubles

import cockpit_lifecycle_websocket
import cockpit_tmux_lifecycle

del jarvis_session_bridge_runtime_test_doubles

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


class ScriptedLifecycleControlWebsocket:
    def __init__(
        self,
        request_messages,
        request_origin="https://lucaszanoni.com",
        request_path=cockpit_lifecycle_websocket.COCKPIT_LIFECYCLE_CONTROL_PATH,
    ):
        self._request_message_iterator = iter(request_messages)
        self.sent_messages = []
        self.close_calls = []
        self.request = types.SimpleNamespace(
            headers={"Origin": request_origin}, path=request_path
        )

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._request_message_iterator)
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, message):
        self.sent_messages.append(message)

    async def close(self, code=1000, reason=""):
        self.close_calls.append((code, reason))
