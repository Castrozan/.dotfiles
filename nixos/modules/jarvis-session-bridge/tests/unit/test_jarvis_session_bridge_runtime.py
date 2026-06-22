import asyncio
import os
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

import pseudoterminal_streams
import server
import settings


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


def test_bridge_rejects_disallowed_origin_with_1008_and_never_spawns(monkeypatch):
    spawn_attempts = []

    async def refuse_to_spawn(*spawn_arguments, **spawn_keyword_arguments):
        spawn_attempts.append(spawn_arguments)
        raise AssertionError("a rejected origin must never spawn a session process")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", refuse_to_spawn)

    origin_gated_settings = settings.JarvisSessionBridgeSettings(
        listen_address="127.0.0.1",
        listen_port=8787,
        session_command=["/bin/sh", "-il"],
        allowed_request_origin="https://lucaszanoni.com",
        terminal_type="xterm-256color",
    )
    disallowed_origin_websocket = RecordingClosingWebsocket("https://evil.test")

    asyncio.run(
        server.bridge_session_over_websocket(
            disallowed_origin_websocket, origin_gated_settings, None
        )
    )

    assert spawn_attempts == []
    assert disallowed_origin_websocket.close_calls
    assert disallowed_origin_websocket.close_calls[0][0] == 1008


def test_output_streamer_forwards_pty_bytes_then_returns_on_eof():
    pseudoterminal_read_descriptor, pseudoterminal_write_descriptor = os.pipe()
    os.set_blocking(pseudoterminal_read_descriptor, False)
    os.write(pseudoterminal_write_descriptor, b"hello-from-pty")
    output_collecting_websocket = OutputCollectingWebsocket()

    async def drive_output_streamer_until_eof():
        event_loop = asyncio.get_running_loop()
        streaming_task = event_loop.create_task(
            pseudoterminal_streams.stream_pseudoterminal_output_to_websocket(
                pseudoterminal_read_descriptor, output_collecting_websocket, event_loop
            )
        )
        await asyncio.sleep(0.05)
        os.close(pseudoterminal_write_descriptor)
        await asyncio.wait_for(streaming_task, timeout=2)

    asyncio.run(drive_output_streamer_until_eof())
    os.close(pseudoterminal_read_descriptor)

    assert "".join(output_collecting_websocket.sent_messages) == "hello-from-pty"


def test_input_streamer_writes_text_and_binary_owner_messages_to_pty():
    pseudoterminal_read_descriptor, pseudoterminal_write_descriptor = os.pipe()
    scripted_input_websocket = ScriptedInputWebsocket(["echo one\n", b"raw-bytes"])

    async def drive_input_streamer_to_completion():
        await pseudoterminal_streams.stream_websocket_input_to_pseudoterminal(
            pseudoterminal_write_descriptor, scripted_input_websocket
        )

    asyncio.run(drive_input_streamer_to_completion())
    os.close(pseudoterminal_write_descriptor)
    received_owner_input = os.read(pseudoterminal_read_descriptor, 4096)
    os.close(pseudoterminal_read_descriptor)

    assert received_owner_input == b"echo one\nraw-bytes"
