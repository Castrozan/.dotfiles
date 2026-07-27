import types

import cockpit_session_bridge_runtime_test_doubles

import cockpit_lifecycle_websocket

del cockpit_session_bridge_runtime_test_doubles


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
