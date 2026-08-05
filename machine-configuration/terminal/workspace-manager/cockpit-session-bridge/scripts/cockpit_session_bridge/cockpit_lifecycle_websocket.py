import json

from cockpit_lifecycle_control import (
    UnsupportedCockpitLifecycleOperation,
    dispatch_cockpit_lifecycle_request,
)
from websockets.exceptions import ConnectionClosed

COCKPIT_LIFECYCLE_CONTROL_PATH = "/cockpit/lifecycle"


async def stream_cockpit_lifecycle_control_over_websocket(
    websocket_connection, multiplexer
):
    async for raw_request_message in websocket_connection:
        lifecycle_reply = await build_cockpit_lifecycle_reply(
            multiplexer, raw_request_message
        )
        try:
            await websocket_connection.send(json.dumps(lifecycle_reply))
        except ConnectionClosed:
            return


async def build_cockpit_lifecycle_reply(multiplexer, raw_request_message):
    lifecycle_request = decode_cockpit_lifecycle_request(raw_request_message)
    if lifecycle_request is None:
        return {"error": "invalid-request"}
    try:
        return await dispatch_cockpit_lifecycle_request(multiplexer, lifecycle_request)
    except UnsupportedCockpitLifecycleOperation as unsupported_operation:
        return {
            "error": "unsupported-operation",
            "operation": str(unsupported_operation),
        }
    except KeyError:
        return {"error": "invalid-request"}


def decode_cockpit_lifecycle_request(raw_request_message):
    if not isinstance(raw_request_message, str):
        return None
    try:
        decoded_request = json.loads(raw_request_message)
    except (ValueError, TypeError):
        return None
    if not isinstance(decoded_request, dict):
        return None
    return decoded_request
