import asyncio
import os
import signal

from cockpit_agent_chat import (
    COCKPIT_AGENT_CHAT_PATH,
    stream_agent_chat_over_websocket,
)
from cockpit_lifecycle_control import build_cockpit_socket_policy
from cockpit_lifecycle_websocket import (
    COCKPIT_LIFECYCLE_CONTROL_PATH,
    stream_cockpit_lifecycle_control_over_websocket,
)
from cockpit_multiplexer_detection import detect_cockpit_multiplexer
from cockpit_session_process import bridge_session_over_websocket
from settings import (
    is_request_origin_allowed,
    read_request_origin,
    read_request_path,
    resolve_bridge_settings,
)


SHUTDOWN_SIGNALS = (signal.SIGTERM, signal.SIGINT)


async def bridge_cockpit_lifecycle_over_websocket(
    websocket_connection, settings, *, subprocess_runner=None
):
    if not is_request_origin_allowed(
        read_request_origin(websocket_connection), settings.allowed_request_origin
    ):
        await websocket_connection.close(code=1008, reason="origin not allowed")
        return
    await stream_cockpit_lifecycle_control_over_websocket(
        websocket_connection,
        await detect_cockpit_multiplexer(
            settings,
            build_cockpit_socket_policy(settings),
            subprocess_runner=subprocess_runner,
        ),
    )


async def bridge_agent_chat_over_websocket(
    websocket_connection, settings, *, subprocess_runner=None
):
    if not is_request_origin_allowed(
        read_request_origin(websocket_connection), settings.allowed_request_origin
    ):
        await websocket_connection.close(code=1008, reason="origin not allowed")
        return
    await stream_agent_chat_over_websocket(
        websocket_connection,
        settings.agent_chat_command,
        subprocess_runner or asyncio.create_subprocess_exec,
    )


async def handle_bridge_websocket_connection(
    websocket_connection, settings, event_loop
):
    request_path = read_request_path(websocket_connection)
    if request_path == COCKPIT_LIFECYCLE_CONTROL_PATH:
        await bridge_cockpit_lifecycle_over_websocket(websocket_connection, settings)
        return
    if request_path == COCKPIT_AGENT_CHAT_PATH:
        await bridge_agent_chat_over_websocket(websocket_connection, settings)
        return
    await bridge_session_over_websocket(websocket_connection, settings, event_loop)


def install_shutdown_signal_handlers(event_loop, shutdown_requested):
    def request_shutdown():
        if not shutdown_requested.done():
            shutdown_requested.set_result(None)

    for shutdown_signal in SHUTDOWN_SIGNALS:
        event_loop.add_signal_handler(shutdown_signal, request_shutdown)


async def serve_cockpit_session_bridge(settings):
    import websockets

    event_loop = asyncio.get_running_loop()
    shutdown_requested = event_loop.create_future()

    async def handle_incoming_websocket_connection(websocket_connection):
        await handle_bridge_websocket_connection(
            websocket_connection, settings, event_loop
        )

    async with websockets.serve(
        handle_incoming_websocket_connection,
        settings.listen_address,
        settings.listen_port,
    ):
        install_shutdown_signal_handlers(event_loop, shutdown_requested)
        await shutdown_requested


def run_cockpit_session_bridge():
    asyncio.run(serve_cockpit_session_bridge(resolve_bridge_settings(os.environ)))
