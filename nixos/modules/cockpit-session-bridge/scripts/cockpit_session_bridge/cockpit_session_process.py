import asyncio
import os
import pty
import signal

from cockpit_lifecycle_control import build_cockpit_socket_policy
from cockpit_multiplexer_detection import detect_cockpit_multiplexer
from pseudoterminal_streams import (
    apply_pseudoterminal_window_size,
    stream_pseudoterminal_output_to_websocket,
    stream_websocket_input_to_pseudoterminal,
)
from settings import (
    is_request_origin_allowed,
    read_request_origin,
    read_request_path,
    read_session_attach_target,
)


SESSION_PROCESS_TERMINATION_TIMEOUT_SECONDS = 5
INITIAL_PSEUDOTERMINAL_COLUMNS = 120
INITIAL_PSEUDOTERMINAL_ROWS = 32


async def resolve_session_command(
    websocket_connection, settings, *, subprocess_runner=None
):
    attach_target = read_session_attach_target(read_request_path(websocket_connection))
    if attach_target is None:
        return settings.session_command
    multiplexer = await detect_cockpit_multiplexer(
        settings,
        build_cockpit_socket_policy(settings),
        subprocess_runner=subprocess_runner,
    )
    return await multiplexer.build_attach_command(attach_target)


async def terminate_session_process(session_process):
    if session_process.returncode is not None:
        return
    try:
        session_process.send_signal(signal.SIGHUP)
    except ProcessLookupError:
        return
    try:
        await asyncio.wait_for(
            session_process.wait(), SESSION_PROCESS_TERMINATION_TIMEOUT_SECONDS
        )
    except TimeoutError:
        try:
            os.killpg(os.getpgid(session_process.pid), signal.SIGKILL)
        except ProcessLookupError:
            return
        await session_process.wait()


async def bridge_session_over_websocket(websocket_connection, settings, event_loop):
    if not is_request_origin_allowed(
        read_request_origin(websocket_connection), settings.allowed_request_origin
    ):
        await websocket_connection.close(code=1008, reason="origin not allowed")
        return

    master_file_descriptor, slave_file_descriptor = pty.openpty()
    os.set_blocking(master_file_descriptor, False)
    apply_pseudoterminal_window_size(
        master_file_descriptor,
        INITIAL_PSEUDOTERMINAL_COLUMNS,
        INITIAL_PSEUDOTERMINAL_ROWS,
    )

    child_environment = dict(os.environ)
    child_environment["TERM"] = settings.terminal_type

    session_process = await asyncio.create_subprocess_exec(
        *await resolve_session_command(websocket_connection, settings),
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
            master_file_descriptor, websocket_connection, event_loop
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
        await terminate_session_process(session_process)
        try:
            os.close(master_file_descriptor)
        except OSError:
            pass
        await websocket_connection.close()
