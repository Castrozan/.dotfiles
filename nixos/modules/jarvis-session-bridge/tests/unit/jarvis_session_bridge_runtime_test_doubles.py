import asyncio
import sys
import types
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "jarvis_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))


class ConnectionClosed(Exception):
    pass


fake_websockets_module = types.ModuleType("websockets")
fake_websockets_exceptions_module = types.ModuleType("websockets.exceptions")
fake_websockets_exceptions_module.ConnectionClosed = ConnectionClosed
fake_websockets_module.exceptions = fake_websockets_exceptions_module
sys.modules.setdefault("websockets", fake_websockets_module)
sys.modules.setdefault("websockets.exceptions", fake_websockets_exceptions_module)


class RecordingClosingWebsocket:
    def __init__(self, request_origin):
        self.request = types.SimpleNamespace(headers={"Origin": request_origin})
        self.close_calls = []

    async def close(self, code=1000, reason=""):
        self.close_calls.append((code, reason))


class OutputCollectingWebsocket:
    def __init__(self):
        self.sent_messages = []

    async def send(self, message):
        self.sent_messages.append(message)


class ScriptedInputWebsocket:
    def __init__(self, owner_messages):
        self._owner_message_iterator = iter(owner_messages)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._owner_message_iterator)
        except StopIteration:
            raise StopAsyncIteration


class FakeSessionProcess:
    def __init__(self, returncode, first_wait_hangs):
        self.returncode = returncode
        self.pid = 4242
        self.signals_sent = []
        self._first_wait_hangs = first_wait_hangs
        self.wait_call_count = 0

    def send_signal(self, signal_number):
        self.signals_sent.append(signal_number)

    async def wait(self):
        self.wait_call_count += 1
        if self._first_wait_hangs and self.wait_call_count == 1:
            await asyncio.sleep(3600)
        return self.returncode
