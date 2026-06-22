import asyncio
import fcntl
import os
import struct
import termios

from settings import parse_owner_control_message
from websockets.exceptions import ConnectionClosed

PSEUDOTERMINAL_READ_CHUNK_SIZE = 65536


def apply_pseudoterminal_window_size(master_file_descriptor, columns, rows):
    packed_window_size = struct.pack("HHHH", rows, columns, 0, 0)
    fcntl.ioctl(master_file_descriptor, termios.TIOCSWINSZ, packed_window_size)


async def stream_pseudoterminal_output_to_websocket(
    master_file_descriptor, websocket_connection, event_loop
):
    output_chunk_queue = asyncio.Queue()

    def enqueue_available_pseudoterminal_output():
        try:
            output_chunk = os.read(
                master_file_descriptor, PSEUDOTERMINAL_READ_CHUNK_SIZE
            )
        except BlockingIOError:
            return
        except OSError:
            output_chunk_queue.put_nowait(None)
            return
        output_chunk_queue.put_nowait(output_chunk or None)

    event_loop.add_reader(
        master_file_descriptor, enqueue_available_pseudoterminal_output
    )
    try:
        while True:
            output_chunk = await output_chunk_queue.get()
            if output_chunk is None:
                return
            try:
                await websocket_connection.send(output_chunk)
            except ConnectionClosed:
                return
    finally:
        event_loop.remove_reader(master_file_descriptor)


async def wait_until_pseudoterminal_writable(master_file_descriptor, event_loop):
    pseudoterminal_writable = event_loop.create_future()

    def mark_pseudoterminal_writable():
        if not pseudoterminal_writable.done():
            pseudoterminal_writable.set_result(None)

    event_loop.add_writer(master_file_descriptor, mark_pseudoterminal_writable)
    try:
        await pseudoterminal_writable
    finally:
        event_loop.remove_writer(master_file_descriptor)


async def write_all_owner_input_to_pseudoterminal(
    master_file_descriptor, owner_input_bytes, event_loop
):
    unwritten_owner_input = memoryview(owner_input_bytes)
    while unwritten_owner_input:
        try:
            written_byte_count = os.write(master_file_descriptor, unwritten_owner_input)
        except BlockingIOError:
            await wait_until_pseudoterminal_writable(master_file_descriptor, event_loop)
            continue
        unwritten_owner_input = unwritten_owner_input[written_byte_count:]


async def stream_websocket_input_to_pseudoterminal(
    master_file_descriptor, websocket_connection, event_loop
):
    async for owner_message in websocket_connection:
        if isinstance(owner_message, str):
            requested_window_size = parse_owner_control_message(owner_message)
            if requested_window_size is None:
                continue
            try:
                apply_pseudoterminal_window_size(
                    master_file_descriptor,
                    requested_window_size.columns,
                    requested_window_size.rows,
                )
            except OSError:
                return
            continue
        try:
            await write_all_owner_input_to_pseudoterminal(
                master_file_descriptor, owner_message, event_loop
            )
        except OSError:
            return
