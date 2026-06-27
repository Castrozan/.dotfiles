import asyncio

from cockpit_lifecycle_websocket_test_doubles import (
    TMUX_EXECUTABLE_PATH,
    RecordingSubprocessRunner,
    ScriptedLifecycleControlWebsocket,
)

import cockpit_lifecycle_websocket
import server
import settings


def test_a_disallowed_origin_on_the_lifecycle_path_is_closed_and_never_dispatches():
    runner = RecordingSubprocessRunner()
    websocket_connection = ScriptedLifecycleControlWebsocket(
        ['{"operation":"list-sessions"}'], request_origin="https://evil.test"
    )
    origin_gated_settings = settings.CockpitSessionBridgeSettings(
        listen_address="127.0.0.1",
        listen_port=8787,
        session_command=["/bin/sh", "-il"],
        allowed_request_origin="https://lucaszanoni.com",
        terminal_type="xterm-256color",
        cockpit_tmux_executable_path=TMUX_EXECUTABLE_PATH,
    )

    asyncio.run(
        server.bridge_cockpit_lifecycle_over_websocket(
            websocket_connection, origin_gated_settings, subprocess_runner=runner
        )
    )

    assert runner.executed_commands == []
    assert websocket_connection.close_calls
    assert websocket_connection.close_calls[0][0] == 1008
    assert websocket_connection.sent_messages == []


def test_the_lifecycle_path_routes_to_the_lifecycle_handler_not_the_session_bridge():
    routed_handlers = []
    websocket_connection = ScriptedLifecycleControlWebsocket(
        [], request_path=cockpit_lifecycle_websocket.COCKPIT_LIFECYCLE_CONTROL_PATH
    )

    asyncio.run(
        _route_recording_which_handler_fires(websocket_connection, routed_handlers)
    )

    assert routed_handlers == ["lifecycle"]


def test_a_non_lifecycle_path_routes_to_the_session_bridge():
    routed_handlers = []
    websocket_connection = ScriptedLifecycleControlWebsocket([], request_path="/")

    asyncio.run(
        _route_recording_which_handler_fires(websocket_connection, routed_handlers)
    )

    assert routed_handlers == ["session"]


async def _route_recording_which_handler_fires(websocket_connection, routed_handlers):
    async def record_lifecycle_route(routed_websocket_connection, routed_settings):
        routed_handlers.append("lifecycle")

    async def record_session_route(
        routed_websocket_connection, routed_settings, routed_event_loop
    ):
        routed_handlers.append("session")

    original_lifecycle_handler = server.bridge_cockpit_lifecycle_over_websocket
    original_session_handler = server.bridge_session_over_websocket
    server.bridge_cockpit_lifecycle_over_websocket = record_lifecycle_route
    server.bridge_session_over_websocket = record_session_route
    try:
        await server.handle_bridge_websocket_connection(
            websocket_connection, None, None
        )
    finally:
        server.bridge_cockpit_lifecycle_over_websocket = original_lifecycle_handler
        server.bridge_session_over_websocket = original_session_handler
