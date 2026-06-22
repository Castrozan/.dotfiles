import asyncio
import os
import pty
import signal

from pseudoterminal_streams import (
    stream_pseudoterminal_output_to_websocket,
    stream_websocket_input_to_pseudoterminal,
)
from settings import (
    is_request_origin_allowed,
    read_request_origin,
    resolve_bridge_settings,
)


async def bridge_session_over_websocket(websocket_connection, settings, event_loop):
    if not is_request_origin_allowed(
        read_request_origin(websocket_connection), settings.allowed_request_origin
    ):
        await websocket_connection.close(code=1008, reason="origin not allowed")
        return

    master_file_descriptor, slave_file_descriptor = pty.openpty()
    os.set_blocking(master_file_descriptor, False)

    child_environment = dict(os.environ)
    child_environment["TERM"] = settings.terminal_type

    session_process = await asyncio.create_subprocess_exec(
        *settings.session_command,
        stdin=slave_file_descriptor,
        stdout=slave_file_descriptor,
        stderr=slave_file_descriptor,
        start_new_session=True,
        env=child_environment,
    )
    os.close(slave_file_descriptor)

    output_task = event_loop.create_task(
        stream_pseudoterminal_output_to_websocket(
            master_file_descriptor, websocket_connection, event_loop
        )
    )
    input_task = event_loop.create_task(
        stream_websocket_input_to_pseudoterminal(
            master_file_descriptor, websocket_connection
        )
    )
    session_wait_task = event_loop.create_task(session_process.wait())

    try:
        await asyncio.wait(
            {output_task, input_task, session_wait_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        for pending_task in (output_task, input_task, session_wait_task):
            if not pending_task.done():
                pending_task.cancel()
        if session_process.returncode is None:
            try:
                session_process.send_signal(signal.SIGHUP)
            except ProcessLookupError:
                pass
        try:
            os.close(master_file_descriptor)
        except OSError:
            pass
        await websocket_connection.close()


async def serve_jarvis_session_bridge(settings):
    import websockets

    event_loop = asyncio.get_running_loop()

    async def handle_session_connection(websocket_connection):
        await bridge_session_over_websocket(websocket_connection, settings, event_loop)

    async with websockets.serve(
        handle_session_connection, settings.listen_address, settings.listen_port
    ):
        await asyncio.Future()


def run_jarvis_session_bridge():
    asyncio.run(serve_jarvis_session_bridge(resolve_bridge_settings(os.environ)))
