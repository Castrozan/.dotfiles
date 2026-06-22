import json
from dataclasses import dataclass

DEFAULT_SESSION_COMMAND = ["/bin/sh", "-il"]
DEFAULT_LISTEN_ADDRESS = "127.0.0.1"
DEFAULT_LISTEN_PORT = 8787
DEFAULT_ALLOWED_REQUEST_ORIGIN = "https://lucaszanoni.com"
DEFAULT_TERMINAL_TYPE = "xterm-256color"
MAXIMUM_PSEUDOTERMINAL_DIMENSION = 10000


@dataclass(frozen=True)
class JarvisSessionBridgeSettings:
    listen_address: str
    listen_port: int
    session_command: list
    allowed_request_origin: str
    terminal_type: str


@dataclass(frozen=True)
class PseudoterminalWindowSizeRequest:
    columns: int
    rows: int


def parse_owner_control_message(raw_text_message):
    try:
        decoded_control_message = json.loads(raw_text_message)
    except (ValueError, TypeError):
        return None
    if not isinstance(decoded_control_message, dict):
        return None
    if decoded_control_message.get("type") != "resize":
        return None
    requested_columns = decoded_control_message.get("columns")
    requested_rows = decoded_control_message.get("rows")
    if not _is_valid_pseudoterminal_dimension(
        requested_columns
    ) or not _is_valid_pseudoterminal_dimension(requested_rows):
        return None
    return PseudoterminalWindowSizeRequest(
        columns=requested_columns, rows=requested_rows
    )


def _is_valid_pseudoterminal_dimension(candidate_dimension):
    return (
        isinstance(candidate_dimension, int)
        and not isinstance(candidate_dimension, bool)
        and 0 < candidate_dimension <= MAXIMUM_PSEUDOTERMINAL_DIMENSION
    )


def parse_session_command(raw_session_command_json):
    if not raw_session_command_json:
        return list(DEFAULT_SESSION_COMMAND)
    decoded_session_command = json.loads(raw_session_command_json)
    if not isinstance(decoded_session_command, list) or not all(
        isinstance(command_argument, str)
        for command_argument in decoded_session_command
    ):
        raise ValueError("session command must be a JSON array of strings")
    if not decoded_session_command:
        raise ValueError("session command must not be empty")
    return decoded_session_command


def resolve_bridge_settings(process_environment):
    return JarvisSessionBridgeSettings(
        listen_address=process_environment.get(
            "JARVIS_SESSION_BRIDGE_LISTEN_ADDRESS", DEFAULT_LISTEN_ADDRESS
        ),
        listen_port=int(
            process_environment.get(
                "JARVIS_SESSION_BRIDGE_LISTEN_PORT", str(DEFAULT_LISTEN_PORT)
            )
        ),
        session_command=parse_session_command(
            process_environment.get("JARVIS_SESSION_BRIDGE_COMMAND_JSON", "")
        ),
        allowed_request_origin=process_environment.get(
            "JARVIS_SESSION_BRIDGE_ALLOWED_ORIGIN", DEFAULT_ALLOWED_REQUEST_ORIGIN
        ),
        terminal_type=DEFAULT_TERMINAL_TYPE,
    )


def is_request_origin_allowed(request_origin, allowed_request_origin):
    if not allowed_request_origin:
        return True
    return request_origin == allowed_request_origin


def read_request_origin(websocket_connection):
    connection_request = getattr(websocket_connection, "request", None)
    if connection_request is not None:
        return connection_request.headers.get("Origin", "")
    legacy_request_headers = getattr(websocket_connection, "request_headers", None)
    if legacy_request_headers is not None:
        return legacy_request_headers.get("Origin", "")
    return ""
