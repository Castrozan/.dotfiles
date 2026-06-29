import asyncio
from dataclasses import dataclass

from cockpit_tmux_commands import (
    build_list_sessions_command,
    build_list_windows_command,
)

DEFAULT_COCKPIT_TMUX_SOCKET_NAME = "cockpit"
SESSION_INVENTORY_FIELD_SEPARATOR = "\t"


@dataclass(frozen=True)
class CockpitTmuxWindow:
    window_identifier: str
    window_title: str
    pane_current_command: str = ""


@dataclass(frozen=True)
class CockpitTmuxSession:
    session_name: str
    windows: tuple


@dataclass(frozen=True)
class CockpitTmuxCommandResult:
    exit_code: int
    standard_output: str
    standard_error: str


def parse_cockpit_session_inventory(list_sessions_output, list_windows_output):
    windows_by_session_name = {}
    for window_line in _non_empty_output_lines(list_windows_output):
        session_name, window = _parse_window_inventory_line(window_line)
        windows_by_session_name.setdefault(session_name, []).append(window)
    return [
        CockpitTmuxSession(
            session_name=session_name,
            windows=tuple(windows_by_session_name.get(session_name, [])),
        )
        for session_name in _non_empty_output_lines(list_sessions_output)
    ]


async def list_cockpit_sessions(
    tmux_executable_path,
    enumeration_socket_name,
    *,
    remote_ssh_host="",
    subprocess_runner=None,
):
    runner = subprocess_runner or run_tmux_subprocess_command
    list_sessions_result = await runner(
        build_list_sessions_command(
            tmux_executable_path,
            enumeration_socket_name,
            remote_ssh_host=remote_ssh_host,
        )
    )
    list_windows_result = await runner(
        build_list_windows_command(
            tmux_executable_path,
            enumeration_socket_name,
            remote_ssh_host=remote_ssh_host,
        )
    )
    return parse_cockpit_session_inventory(
        list_sessions_result.standard_output, list_windows_result.standard_output
    )


async def run_tmux_subprocess_command(tmux_command):
    tmux_process = await asyncio.create_subprocess_exec(
        *tmux_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    standard_output_bytes, standard_error_bytes = await tmux_process.communicate()
    return CockpitTmuxCommandResult(
        exit_code=tmux_process.returncode,
        standard_output=standard_output_bytes.decode(),
        standard_error=standard_error_bytes.decode(),
    )


def _non_empty_output_lines(command_output):
    return [output_line for output_line in command_output.splitlines() if output_line]


def _parse_window_inventory_line(window_line):
    inventory_fields = window_line.split(SESSION_INVENTORY_FIELD_SEPARATOR, 3)
    session_name = inventory_fields[0]
    window_identifier = inventory_fields[1] if len(inventory_fields) > 1 else ""
    pane_current_command = inventory_fields[2] if len(inventory_fields) > 2 else ""
    window_title = inventory_fields[3] if len(inventory_fields) > 3 else ""
    return session_name, CockpitTmuxWindow(
        window_identifier=window_identifier,
        window_title=window_title,
        pane_current_command=pane_current_command,
    )
