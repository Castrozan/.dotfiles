import asyncio
import os

from websockets.exceptions import ConnectionClosed

PSEUDOTERMINAL_READ_CHUNK_SIZE = 65536


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
                await websocket_connection.send(
                    output_chunk.decode("utf-8", errors="replace")
                )
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
        owner_input_bytes = (
            owner_message.encode("utf-8")
            if isinstance(owner_message, str)
            else owner_message
        )
        try:
            await write_all_owner_input_to_pseudoterminal(
                master_file_descriptor, owner_input_bytes, event_loop
            )
        except OSError:
            return
