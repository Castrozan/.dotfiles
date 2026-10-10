import asyncio
from unittest.mock import AsyncMock

import pytest

from cockpit_lifecycle_websocket_test_doubles import ScriptedLifecycleControlWebsocket
import server
import settings


@pytest.mark.parametrize(
    "request_path", ["/cockpit/agent-chat", "/cockpit/jarvis-session/", "/unknown"]
)
def test_removed_and_unknown_routes_never_open_a_terminal(request_path, monkeypatch):
    bridge_session = AsyncMock()
    monkeypatch.setattr(server, "bridge_session_over_websocket", bridge_session)
    connection = ScriptedLifecycleControlWebsocket([], request_path=request_path)

    asyncio.run(
        server.handle_bridge_websocket_connection(
            connection, settings.resolve_bridge_settings({}), None
        )
    )

    bridge_session.assert_not_called()
    assert connection.close_calls == [(1008, "unknown route")]


def test_generic_session_route_preserves_terminal_selection(monkeypatch):
    bridge_session = AsyncMock()
    monkeypatch.setattr(server, "bridge_session_over_websocket", bridge_session)
    connection = ScriptedLifecycleControlWebsocket(
        [], request_path="/cockpit/terminal-session/?terminal=term_example"
    )
    bridge_settings = settings.resolve_bridge_settings({})

    asyncio.run(
        server.handle_bridge_websocket_connection(connection, bridge_settings, None)
    )

    bridge_session.assert_awaited_once_with(connection, bridge_settings, None)
