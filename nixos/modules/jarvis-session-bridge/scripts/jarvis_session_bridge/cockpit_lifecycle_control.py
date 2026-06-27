from cockpit_tmux_lifecycle import (
    build_close_session_command,
    build_close_window_command,
    build_open_session_command,
    build_open_window_command,
    build_rename_session_command,
    list_cockpit_sessions,
    run_tmux_subprocess_command,
)

COCKPIT_LIFECYCLE_CONTROL_MESSAGE_TYPE = "cockpit-tmux-lifecycle"


class UnsupportedCockpitLifecycleOperation(Exception):
    pass


async def dispatch_cockpit_lifecycle_request(
    tmux_executable_path, lifecycle_request, *, subprocess_runner=None
):
    subprocess_runner = subprocess_runner or run_tmux_subprocess_command
    requested_operation = lifecycle_request.get("operation")
    if requested_operation == "list-sessions":
        return await _list_sessions_response(tmux_executable_path, subprocess_runner)
    build_mutation_command = _MUTATION_COMMAND_BUILDERS.get(requested_operation)
    if build_mutation_command is None:
        raise UnsupportedCockpitLifecycleOperation(requested_operation)
    return await _run_mutation_response(
        requested_operation,
        build_mutation_command(tmux_executable_path, lifecycle_request),
        subprocess_runner,
    )


async def _list_sessions_response(tmux_executable_path, subprocess_runner):
    sessions = await list_cockpit_sessions(
        tmux_executable_path, subprocess_runner=subprocess_runner
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
            }
            for window in session.windows
        ],
    }


def _build_open_session_mutation_command(tmux_executable_path, lifecycle_request):
    return build_open_session_command(
        tmux_executable_path, lifecycle_request["sessionName"]
    )


def _build_rename_session_mutation_command(tmux_executable_path, lifecycle_request):
    return build_rename_session_command(
        tmux_executable_path,
        lifecycle_request["currentSessionName"],
        lifecycle_request["newSessionName"],
    )


def _build_close_session_mutation_command(tmux_executable_path, lifecycle_request):
    return build_close_session_command(
        tmux_executable_path, lifecycle_request["sessionName"]
    )


def _build_open_window_mutation_command(tmux_executable_path, lifecycle_request):
    return build_open_window_command(
        tmux_executable_path,
        lifecycle_request["sessionName"],
        lifecycle_request["windowTitle"],
        lifecycle_request.get("agentLaunchCommand", ""),
    )


def _build_close_window_mutation_command(tmux_executable_path, lifecycle_request):
    return build_close_window_command(
        tmux_executable_path, lifecycle_request["windowIdentifier"]
    )


_MUTATION_COMMAND_BUILDERS = {
    "open-session": _build_open_session_mutation_command,
    "rename-session": _build_rename_session_mutation_command,
    "close-session": _build_close_session_mutation_command,
    "open-window": _build_open_window_mutation_command,
    "close-window": _build_close_window_mutation_command,
}
