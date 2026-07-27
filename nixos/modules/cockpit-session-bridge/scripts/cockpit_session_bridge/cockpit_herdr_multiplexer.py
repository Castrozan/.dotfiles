import shlex

from cockpit_herdr_commands import (
    LAUNCH_COMMAND_SHELL,
    CockpitHerdrConnection,
    build_close_tab_command,
    build_close_workspace_command,
    build_create_tab_command,
    build_create_workspace_command,
    build_focus_tab_command,
    build_local_attach_session_command,
    build_local_focus_workspace_command,
    build_rename_workspace_command,
    build_runtime_snapshot_command,
    build_start_agent_command,
)
from cockpit_herdr_snapshot import (
    parse_herdr_runtime_snapshot,
    parse_herdr_workspace_identifiers,
)
from cockpit_multiplexer_port import (
    CockpitMultiplexerCommandResult,
    run_multiplexer_subprocess_command,
    wrap_command_for_remote_ssh,
)

HERDR_MULTIPLEXER_NAME = "herdr"
DEFAULT_HERDR_SESSION_NAME = "default"
DISCARDED_COMMAND_OUTPUT = ">/dev/null 2>&1"


class CockpitHerdrMultiplexer:
    multiplexer_name = HERDR_MULTIPLEXER_NAME

    def __init__(
        self,
        herdr_executable_path,
        herdr_session_name=DEFAULT_HERDR_SESSION_NAME,
        *,
        remote_ssh_host="",
        subprocess_runner=None,
    ):
        self._connection = CockpitHerdrConnection(
            herdr_executable_path=herdr_executable_path,
            herdr_session_name=herdr_session_name,
            remote_ssh_host=remote_ssh_host,
        )
        self._subprocess_runner = (
            subprocess_runner or run_multiplexer_subprocess_command
        )

    async def list_sessions(self):
        return parse_herdr_runtime_snapshot(await self._read_runtime_snapshot())

    async def open_session(self, session_name):
        return await self._subprocess_runner(
            build_create_workspace_command(self._connection, session_name)
        )

    async def rename_session(self, current_session_name, new_session_name):
        return await self._run_against_workspace(
            current_session_name,
            lambda workspace_identifier: build_rename_workspace_command(
                self._connection, workspace_identifier, new_session_name
            ),
        )

    async def close_session(self, session_name):
        return await self._run_against_workspace(
            session_name,
            lambda workspace_identifier: build_close_workspace_command(
                self._connection, workspace_identifier
            ),
        )

    async def open_window(self, session_name, window_title, agent_launch_command):
        return await self._run_against_workspace(
            session_name,
            lambda workspace_identifier: self._build_open_window_command(
                workspace_identifier, window_title, agent_launch_command
            ),
        )

    async def close_window(self, window_identifier):
        return await self._subprocess_runner(
            build_close_tab_command(self._connection, window_identifier)
        )

    async def select_window(self, window_identifier):
        return await self._subprocess_runner(
            build_focus_tab_command(self._connection, window_identifier)
        )

    async def build_attach_command(self, attach_target):
        attach_command = build_local_attach_session_command(self._connection)
        workspace_identifier = await self._resolve_workspace_identifier(attach_target)
        if workspace_identifier is not None:
            focus_command = build_local_focus_workspace_command(
                self._connection, workspace_identifier
            )
            attach_command = [
                LAUNCH_COMMAND_SHELL,
                "-c",
                f"{shlex.join(focus_command)} {DISCARDED_COMMAND_OUTPUT}"
                f"; exec {shlex.join(attach_command)}",
            ]
        return wrap_command_for_remote_ssh(
            attach_command,
            self._connection.remote_ssh_host,
            allocate_remote_pseudoterminal=True,
        )

    def _build_open_window_command(
        self, workspace_identifier, window_title, agent_launch_command
    ):
        if agent_launch_command:
            return build_start_agent_command(
                self._connection,
                workspace_identifier,
                window_title,
                agent_launch_command,
            )
        return build_create_tab_command(
            self._connection, workspace_identifier, window_title
        )

    async def _read_runtime_snapshot(self):
        snapshot_result = await self._subprocess_runner(
            build_runtime_snapshot_command(self._connection)
        )
        return snapshot_result.standard_output

    async def _resolve_workspace_identifier(self, session_name):
        return parse_herdr_workspace_identifiers(
            await self._read_runtime_snapshot()
        ).get(session_name)

    async def _run_against_workspace(self, session_name, build_workspace_command):
        workspace_identifier = await self._resolve_workspace_identifier(session_name)
        if workspace_identifier is None:
            return CockpitMultiplexerCommandResult(
                exit_code=1,
                standard_output="",
                standard_error=f"no herdr workspace labelled {session_name}",
            )
        return await self._subprocess_runner(
            build_workspace_command(workspace_identifier)
        )
