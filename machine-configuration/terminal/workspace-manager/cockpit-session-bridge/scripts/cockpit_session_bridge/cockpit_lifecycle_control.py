from dataclasses import dataclass

DEFAULT_COCKPIT_TMUX_SOCKET_NAME = "cockpit"

COCKPIT_LIFECYCLE_CONTROL_MESSAGE_TYPE = "cockpit-tmux-lifecycle"


@dataclass(frozen=True)
class CockpitTmuxSocketPolicy:
    enumeration_socket_name: str = DEFAULT_COCKPIT_TMUX_SOCKET_NAME
    mutation_socket_name: str = DEFAULT_COCKPIT_TMUX_SOCKET_NAME
    remote_ssh_host: str = ""


def build_cockpit_socket_policy(settings):
    return CockpitTmuxSocketPolicy(
        enumeration_socket_name=settings.cockpit_tmux_enumeration_socket_name,
        mutation_socket_name=settings.cockpit_tmux_mutation_socket_name,
        remote_ssh_host=settings.cockpit_tmux_remote_ssh_host,
    )


class UnsupportedCockpitLifecycleOperation(Exception):
    pass


async def dispatch_cockpit_lifecycle_request(multiplexer, lifecycle_request):
    requested_operation = lifecycle_request.get("operation")
    if requested_operation == "list-sessions":
        return {
            "operation": "list-sessions",
            "sessions": [
                _serialize_session(session)
                for session in await multiplexer.list_sessions()
            ],
        }
    run_mutation = _MUTATION_RUNNERS.get(requested_operation)
    if run_mutation is None:
        raise UnsupportedCockpitLifecycleOperation(requested_operation)
    command_result = await run_mutation(multiplexer, lifecycle_request)
    return {
        "operation": requested_operation,
        "exitCode": command_result.exit_code,
        "standardError": command_result.standard_error,
    }


def _serialize_session(session):
    return {
        "sessionName": session.session_name,
        "windows": [
            {
                "windowIdentifier": window.window_identifier,
                "windowTitle": window.window_title,
                "agentDriver": window.agent_driver or None,
                "terminalIdentifier": window.terminal_identifier,
            }
            for window in session.windows
        ],
    }


_MUTATION_RUNNERS = {
    "open-session": lambda multiplexer, request: multiplexer.open_session(
        request["sessionName"]
    ),
    "rename-session": lambda multiplexer, request: multiplexer.rename_session(
        request["currentSessionName"], request["newSessionName"]
    ),
    "close-session": lambda multiplexer, request: multiplexer.close_session(
        request["sessionName"]
    ),
    "open-window": lambda multiplexer, request: multiplexer.open_window(
        request["sessionName"],
        request["windowTitle"],
        request.get("agentLaunchCommand", ""),
    ),
    "close-window": lambda multiplexer, request: multiplexer.close_window(
        request["windowIdentifier"]
    ),
}
