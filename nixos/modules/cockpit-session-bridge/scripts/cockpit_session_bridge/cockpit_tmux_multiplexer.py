from cockpit_multiplexer_port import (
    CockpitMultiplexerSession,
    CockpitMultiplexerWindow,
    run_multiplexer_subprocess_command,
)
from cockpit_tmux_commands import (
    build_attach_session_command,
    build_close_session_command,
    build_close_window_command,
    build_list_sessions_command,
    build_list_windows_command,
    build_open_session_command,
    build_open_window_command,
    build_rename_session_command,
    build_select_window_command,
)

TMUX_MULTIPLEXER_NAME = "tmux"
SESSION_INVENTORY_FIELD_SEPARATOR = "\t"
AGENT_DRIVER_BY_PANE_CURRENT_COMMAND = {
    "claude": "claude",
    "codex": "codex",
}


def parse_tmux_session_inventory(list_sessions_output, list_windows_output):
    windows_by_session_name = {}
    for window_line in _non_empty_output_lines(list_windows_output):
        session_name, window = _parse_window_inventory_line(window_line)
        windows_by_session_name.setdefault(session_name, []).append(window)
    return [
        CockpitMultiplexerSession(
            session_name=session_name,
            windows=tuple(windows_by_session_name.get(session_name, [])),
        )
        for session_name in _non_empty_output_lines(list_sessions_output)
    ]


def _non_empty_output_lines(command_output):
    return [output_line for output_line in command_output.splitlines() if output_line]


def _parse_window_inventory_line(window_line):
    inventory_fields = window_line.split(SESSION_INVENTORY_FIELD_SEPARATOR, 3)
    session_name = inventory_fields[0]
    window_identifier = inventory_fields[1] if len(inventory_fields) > 1 else ""
    pane_current_command = inventory_fields[2] if len(inventory_fields) > 2 else ""
    window_title = inventory_fields[3] if len(inventory_fields) > 3 else ""
    return session_name, CockpitMultiplexerWindow(
        window_identifier=window_identifier,
        window_title=window_title,
        agent_driver=AGENT_DRIVER_BY_PANE_CURRENT_COMMAND.get(pane_current_command, ""),
    )


class CockpitTmuxMultiplexer:
    multiplexer_name = TMUX_MULTIPLEXER_NAME

    def __init__(
        self,
        tmux_executable_path,
        socket_policy,
        *,
        subprocess_runner=None,
    ):
        self._tmux_executable_path = tmux_executable_path
        self._socket_policy = socket_policy
        self._subprocess_runner = (
            subprocess_runner or run_multiplexer_subprocess_command
        )

    async def list_sessions(self):
        list_sessions_result = await self._subprocess_runner(
            build_list_sessions_command(
                self._tmux_executable_path,
                self._socket_policy.enumeration_socket_name,
                remote_ssh_host=self._socket_policy.remote_ssh_host,
            )
        )
        list_windows_result = await self._subprocess_runner(
            build_list_windows_command(
                self._tmux_executable_path,
                self._socket_policy.enumeration_socket_name,
                remote_ssh_host=self._socket_policy.remote_ssh_host,
            )
        )
        return parse_tmux_session_inventory(
            list_sessions_result.standard_output, list_windows_result.standard_output
        )

    async def open_session(self, session_name):
        return await self._subprocess_runner(
            build_open_session_command(
                self._tmux_executable_path,
                self._socket_policy.mutation_socket_name,
                session_name,
            )
        )

    async def rename_session(self, current_session_name, new_session_name):
        return await self._subprocess_runner(
            build_rename_session_command(
                self._tmux_executable_path,
                self._socket_policy.mutation_socket_name,
                current_session_name,
                new_session_name,
            )
        )

    async def close_session(self, session_name):
        return await self._subprocess_runner(
            build_close_session_command(
                self._tmux_executable_path,
                self._socket_policy.mutation_socket_name,
                session_name,
            )
        )

    async def open_window(self, session_name, window_title, agent_launch_command):
        return await self._subprocess_runner(
            build_open_window_command(
                self._tmux_executable_path,
                self._socket_policy.mutation_socket_name,
                session_name,
                window_title,
                agent_launch_command,
            )
        )

    async def close_window(self, window_identifier):
        return await self._subprocess_runner(
            build_close_window_command(
                self._tmux_executable_path,
                self._socket_policy.mutation_socket_name,
                window_identifier,
            )
        )

    async def select_window(self, window_identifier):
        return await self._subprocess_runner(
            build_select_window_command(
                self._tmux_executable_path,
                self._socket_policy.enumeration_socket_name,
                window_identifier,
                remote_ssh_host=self._socket_policy.remote_ssh_host,
            )
        )

    async def build_attach_command(self, attach_target):
        return build_attach_session_command(
            self._tmux_executable_path,
            self._socket_policy.enumeration_socket_name,
            attach_target,
            remote_ssh_host=self._socket_policy.remote_ssh_host,
        )
