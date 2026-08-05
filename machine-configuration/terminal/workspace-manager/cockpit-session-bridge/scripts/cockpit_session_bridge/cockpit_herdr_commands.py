import re
from dataclasses import dataclass

from cockpit_multiplexer_port import wrap_command_for_remote_ssh

REMOTE_HERDR_EXECUTABLE = "herdr"
LAUNCH_COMMAND_SHELL = "/bin/sh"
LAUNCH_COMMAND_SHELL_OPTIONS = "-lc"
HERDR_TERMINAL_IDENTIFIER_PATTERN = re.compile(r"\Aterm_[0-9a-f]+\Z")


def is_herdr_terminal_identifier(candidate_identifier):
    return bool(
        isinstance(candidate_identifier, str)
        and HERDR_TERMINAL_IDENTIFIER_PATTERN.match(candidate_identifier)
    )


@dataclass(frozen=True)
class CockpitHerdrConnection:
    herdr_executable_path: str
    herdr_session_name: str = ""
    remote_ssh_host: str = ""

    def build_local_command(self, *herdr_arguments, include_session=True):
        herdr_command_executable = (
            REMOTE_HERDR_EXECUTABLE
            if self.remote_ssh_host
            else self.herdr_executable_path
        )
        if include_session and self.herdr_session_name:
            return [
                herdr_command_executable,
                "--session",
                self.herdr_session_name,
                *herdr_arguments,
            ]
        return [herdr_command_executable, *herdr_arguments]

    def build_command(self, *herdr_arguments, include_session=True):
        return wrap_command_for_remote_ssh(
            self.build_local_command(*herdr_arguments, include_session=include_session),
            self.remote_ssh_host,
        )


def build_server_status_command(connection):
    return connection.build_command("status", "server", include_session=False)


def build_runtime_snapshot_command(connection):
    return connection.build_command("api", "snapshot")


def build_create_workspace_command(connection, workspace_label):
    return connection.build_command(
        "workspace", "create", "--label", workspace_label, "--no-focus"
    )


def build_rename_workspace_command(connection, workspace_identifier, workspace_label):
    return connection.build_command(
        "workspace", "rename", workspace_identifier, workspace_label
    )


def build_close_workspace_command(connection, workspace_identifier):
    return connection.build_command("workspace", "close", workspace_identifier)


def build_create_tab_command(connection, workspace_identifier, tab_label):
    return connection.build_command(
        "tab",
        "create",
        "--workspace",
        workspace_identifier,
        "--label",
        tab_label,
        "--no-focus",
    )


def build_start_agent_command(
    connection, workspace_identifier, agent_name, agent_launch_command
):
    return connection.build_command(
        "agent",
        "start",
        agent_name,
        "--workspace",
        workspace_identifier,
        "--no-focus",
        "--",
        LAUNCH_COMMAND_SHELL,
        LAUNCH_COMMAND_SHELL_OPTIONS,
        agent_launch_command,
    )


def build_close_tab_command(connection, tab_identifier):
    return connection.build_command("tab", "close", tab_identifier)


def build_local_attach_terminal_command(connection, terminal_identifier):
    if not is_herdr_terminal_identifier(terminal_identifier):
        raise ValueError(f"not a herdr terminal identifier: {terminal_identifier!r}")
    return connection.build_local_command(
        "terminal", "attach", terminal_identifier, include_session=False
    )
