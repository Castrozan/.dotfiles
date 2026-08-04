import shlex
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from agent_session.harness import (
    find_agent_session,
    resume_command_for,
    session_identifier_from_command,
)

from .codex_rollout_lookup import codex_session_identifier_for_working_directory

CLAUDE_SESSION_IDENTIFIER_ENVIRONMENT_VARIABLE = "CLAUDE_CODE_SESSION_ID"
CLAWDE_AGENT_NAME_ENVIRONMENT_VARIABLE = "CLAWDE_AGENT_NAME"
MACHINE_NAME_ENVIRONMENT_VARIABLE = "AGENT_COMMIT_PROVENANCE_MACHINE"


@dataclass(frozen=True)
class AgentSessionIdentity:
    harness_name: str
    machine_name: str
    session_identifier: str | None
    agent_name: str | None

    def resume_command(self) -> str | None:
        if self.session_identifier is None:
            return None
        return shlex.join(
            resume_command_for(self.harness_name, self.session_identifier)
        )


def machine_name_from_environment(environment: Mapping[str, str]) -> str:
    configured_machine_name = environment.get(
        MACHINE_NAME_ENVIRONMENT_VARIABLE, ""
    ).strip()
    if configured_machine_name:
        return configured_machine_name
    return socket.gethostname().split(".")[0]


def agent_name_from_environment(environment: Mapping[str, str]) -> str | None:
    return environment.get(CLAWDE_AGENT_NAME_ENVIRONMENT_VARIABLE, "").strip() or None


def harness_and_session_from_environment(
    environment: Mapping[str, str],
) -> tuple[str, str] | None:
    claude_session_identifier = environment.get(
        CLAUDE_SESSION_IDENTIFIER_ENVIRONMENT_VARIABLE, ""
    ).strip()
    if claude_session_identifier:
        return "claude", claude_session_identifier
    return None


def harness_and_session_from_process_ancestry(
    process_identifier: int, working_directory: Path
) -> tuple[str, str | None] | None:
    agent_session = find_agent_session(process_identifier)
    if agent_session is None:
        return None
    _harness_process_identifier, harness_name, command_line = agent_session
    session_identifier = session_identifier_from_command(harness_name, command_line)
    if session_identifier is None and harness_name == "codex":
        session_identifier = codex_session_identifier_for_working_directory(
            working_directory
        )
    return harness_name, session_identifier


def resolve_agent_session_identity(
    environment: Mapping[str, str],
    process_identifier: int,
    working_directory: Path,
) -> AgentSessionIdentity | None:
    harness_and_session = harness_and_session_from_environment(
        environment
    ) or harness_and_session_from_process_ancestry(
        process_identifier, working_directory
    )
    if harness_and_session is None:
        return None
    harness_name, session_identifier = harness_and_session
    return AgentSessionIdentity(
        harness_name=harness_name,
        machine_name=machine_name_from_environment(environment),
        session_identifier=session_identifier,
        agent_name=agent_name_from_environment(environment),
    )
