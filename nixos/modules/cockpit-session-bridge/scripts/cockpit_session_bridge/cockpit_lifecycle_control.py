from dataclasses import dataclass

from cockpit_tmux_lifecycle import (
    DEFAULT_COCKPIT_TMUX_SOCKET_NAME,
    build_close_session_command,
    build_close_window_command,
    build_open_session_command,
    build_open_window_command,
    build_rename_session_command,
    list_cockpit_sessions,
    run_tmux_subprocess_command,
)

COCKPIT_LIFECYCLE_CONTROL_MESSAGE_TYPE = "cockpit-tmux-lifecycle"

AGENT_DRIVER_BY_PANE_CURRENT_COMMAND = {
    "claude": "claude",
    "codex": "codex",
}


@dataclass(frozen=True)
class CockpitTmuxSocketPolicy:
    enumeration_socket_name: str = DEFAULT_COCKPIT_TMUX_SOCKET_NAME
    mutation_socket_name: str = DEFAULT_COCKPIT_TMUX_SOCKET_NAME


class UnsupportedCockpitLifecycleOperation(Exception):
    pass


async def dispatch_cockpit_lifecycle_request(
    tmux_executable_path, socket_policy, lifecycle_request, *, subprocess_runner=None
):
    subprocess_runner = subprocess_runner or run_tmux_subprocess_command
    requested_operation = lifecycle_request.get("operation")
    if requested_operation == "list-sessions":
        return await _list_sessions_response(
            tmux_executable_path, socket_policy, subprocess_runner
        )
    build_mutation_command = _MUTATION_COMMAND_BUILDERS.get(requested_operation)
    if build_mutation_command is None:
        raise UnsupportedCockpitLifecycleOperation(requested_operation)
    return await _run_mutation_response(
        requested_operation,
        build_mutation_command(
            tmux_executable_path,
            socket_policy.mutation_socket_name,
            lifecycle_request,
        ),
        subprocess_runner,
    )


async def _list_sessions_response(
    tmux_executable_path, socket_policy, subprocess_runner
):
    sessions = await list_cockpit_sessions(
        tmux_executable_path,
        socket_policy.enumeration_socket_name,
        subprocess_runner=subprocess_runner,
    )
    return {
        "operation": "list-sessions",
        "sessions": [_serialize_session(session) for session in sessions],
    }


async def _run_mutation_response(
    requested_operation, mutation_command, subprocess_runner
):
    command_result = await subprocess_runner(mutation_command)
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
                "agentDriver": _detect_agent_driver(window.pane_current_command),
            }
            for window in session.windows
        ],
    }


def _detect_agent_driver(pane_current_command):
    return AGENT_DRIVER_BY_PANE_CURRENT_COMMAND.get(pane_current_command)


def _build_open_session_mutation_command(
    tmux_executable_path, mutation_socket_name, lifecycle_request
):
    return build_open_session_command(
        tmux_executable_path, mutation_socket_name, lifecycle_request["sessionName"]
    )


def _build_rename_session_mutation_command(
    tmux_executable_path, mutation_socket_name, lifecycle_request
):
    return build_rename_session_command(
        tmux_executable_path,
        mutation_socket_name,
        lifecycle_request["currentSessionName"],
        lifecycle_request["newSessionName"],
    )


def _build_close_session_mutation_command(
    tmux_executable_path, mutation_socket_name, lifecycle_request
):
    return build_close_session_command(
        tmux_executable_path, mutation_socket_name, lifecycle_request["sessionName"]
    )


def _build_open_window_mutation_command(
    tmux_executable_path, mutation_socket_name, lifecycle_request
):
    return build_open_window_command(
        tmux_executable_path,
        mutation_socket_name,
        lifecycle_request["sessionName"],
        lifecycle_request["windowTitle"],
        lifecycle_request.get("agentLaunchCommand", ""),
    )


def _build_close_window_mutation_command(
    tmux_executable_path, mutation_socket_name, lifecycle_request
):
    return build_close_window_command(
        tmux_executable_path,
        mutation_socket_name,
        lifecycle_request["windowIdentifier"],
    )


_MUTATION_COMMAND_BUILDERS = {
    "open-session": _build_open_session_mutation_command,
    "rename-session": _build_rename_session_mutation_command,
    "close-session": _build_close_session_mutation_command,
    "open-window": _build_open_window_mutation_command,
    "close-window": _build_close_window_mutation_command,
}
