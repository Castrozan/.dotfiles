import asyncio
import os
import pty

from cockpit_session_bridge_runtime_test_doubles import (
    OutputCollectingWebsocket,
    RecordingClosingWebsocket,
    ScriptedInputWebsocket,
)

import pseudoterminal_streams
import server
import settings


def test_bridge_rejects_disallowed_origin_with_1008_and_never_spawns(monkeypatch):
    spawn_attempts = []

    async def refuse_to_spawn(*spawn_arguments, **spawn_keyword_arguments):
        spawn_attempts.append(spawn_arguments)
        raise AssertionError("a rejected origin must never spawn a session process")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", refuse_to_spawn)

    origin_gated_settings = settings.CockpitSessionBridgeSettings(
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

    assert b"".join(output_collecting_websocket.sent_messages) == b"hello-from-pty"


def test_input_streamer_writes_binary_owner_keystrokes_to_pty():
    pseudoterminal_read_descriptor, pseudoterminal_write_descriptor = os.pipe()
    scripted_input_websocket = ScriptedInputWebsocket([b"echo one\n", b"raw-bytes"])

    async def drive_input_streamer_to_completion():
        event_loop = asyncio.get_running_loop()
        await pseudoterminal_streams.stream_websocket_input_to_pseudoterminal(
            pseudoterminal_write_descriptor, scripted_input_websocket, event_loop
        )

    asyncio.run(drive_input_streamer_to_completion())
    os.close(pseudoterminal_write_descriptor)
    received_owner_input = os.read(pseudoterminal_read_descriptor, 4096)
    os.close(pseudoterminal_read_descriptor)

    assert received_owner_input == b"echo one\nraw-bytes"


def test_input_streamer_applies_resize_control_frame_and_never_writes_it_to_pty():
    import fcntl
    import struct
    import termios

    master_file_descriptor, slave_file_descriptor = pty.openpty()
    scripted_input_websocket = ScriptedInputWebsocket(
        ['{"type":"resize","columns":203,"rows":51}', b"after-resize"]
    )

    async def drive_input_streamer_to_completion():
        event_loop = asyncio.get_running_loop()
        await pseudoterminal_streams.stream_websocket_input_to_pseudoterminal(
            master_file_descriptor, scripted_input_websocket, event_loop
        )

    asyncio.run(drive_input_streamer_to_completion())

    applied_rows, applied_columns, _unused_x_pixels, _unused_y_pixels = struct.unpack(
        "HHHH",
        fcntl.ioctl(slave_file_descriptor, termios.TIOCGWINSZ, b"\x00" * 8),
    )
    keystrokes_written_after_the_resize = os.read(master_file_descriptor, 4096)
    os.close(master_file_descriptor)
    os.close(slave_file_descriptor)

    assert (applied_columns, applied_rows) == (203, 51)
    assert keystrokes_written_after_the_resize == b"after-resize"


def test_input_streamer_drains_backpressured_pseudoterminal_without_dropping_input():
    pseudoterminal_read_descriptor, pseudoterminal_write_descriptor = os.pipe()
    os.set_blocking(pseudoterminal_write_descriptor, False)
    os.set_blocking(pseudoterminal_read_descriptor, False)
    large_owner_input = b"x" * (1024 * 1024)
    scripted_input_websocket = ScriptedInputWebsocket([large_owner_input])
    received_input_chunks = []

    async def drive_backpressured_input_streamer():
        event_loop = asyncio.get_running_loop()
        streaming_task = event_loop.create_task(
            pseudoterminal_streams.stream_websocket_input_to_pseudoterminal(
                pseudoterminal_write_descriptor, scripted_input_websocket, event_loop
            )
        )
        received_byte_count = 0
        while received_byte_count < len(large_owner_input):
            await asyncio.sleep(0)
            try:
                drained_chunk = os.read(pseudoterminal_read_descriptor, 65536)
            except BlockingIOError:
                await asyncio.sleep(0.001)
                continue
            received_input_chunks.append(drained_chunk)
            received_byte_count += len(drained_chunk)
        await asyncio.wait_for(streaming_task, timeout=5)

    asyncio.run(drive_backpressured_input_streamer())
    os.close(pseudoterminal_write_descriptor)
    os.close(pseudoterminal_read_descriptor)

    assert b"".join(received_input_chunks) == large_owner_input
