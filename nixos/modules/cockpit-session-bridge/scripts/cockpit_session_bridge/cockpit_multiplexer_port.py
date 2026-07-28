import asyncio
import shlex
from dataclasses import dataclass
from typing import Protocol

NON_INTERACTIVE_SSH_OPTIONS = [
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=accept-new",
    "-o",
    "ConnectTimeout=10",
]


@dataclass(frozen=True)
class CockpitMultiplexerWindow:
    window_identifier: str
    window_title: str
    agent_driver: str = ""


@dataclass(frozen=True)
class CockpitMultiplexerSession:
    session_name: str
    windows: tuple


@dataclass(frozen=True)
class CockpitMultiplexerCommandResult:
    exit_code: int
    standard_output: str
    standard_error: str


class CockpitMultiplexer(Protocol):
    multiplexer_name: str

    async def list_sessions(self): ...

    async def open_session(self, session_name): ...

    async def rename_session(self, current_session_name, new_session_name): ...

    async def close_session(self, session_name): ...

    async def open_window(self, session_name, window_title, agent_launch_command): ...

    async def close_window(self, window_identifier): ...

    async def build_attach_command(self, attach_target): ...


def wrap_command_for_remote_ssh(
    local_command, remote_ssh_host, *, allocate_remote_pseudoterminal=False
):
    if not remote_ssh_host:
        return local_command
    remote_ssh_invocation = ["ssh", *NON_INTERACTIVE_SSH_OPTIONS]
    if allocate_remote_pseudoterminal:
        remote_ssh_invocation.append("-tt")
    remote_ssh_invocation.append(remote_ssh_host)
    return [*remote_ssh_invocation, shlex.join(local_command)]


async def run_multiplexer_subprocess_command(multiplexer_command):
    multiplexer_process = await asyncio.create_subprocess_exec(
        *multiplexer_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    (
        standard_output_bytes,
        standard_error_bytes,
    ) = await multiplexer_process.communicate()
    return CockpitMultiplexerCommandResult(
        exit_code=multiplexer_process.returncode,
        standard_output=standard_output_bytes.decode(),
        standard_error=standard_error_bytes.decode(),
    )
