import subprocess
from pathlib import Path

from .session_identity import AgentSessionIdentity

AGENT_MACHINE_TRAILER_KEY = "Agent-Machine"
AGENT_NAME_TRAILER_KEY = "Agent-Name"
AGENT_RESUME_TRAILER_KEY = "Agent-Resume"

AGENT_PROVENANCE_TRAILER_KEYS = (
    AGENT_MACHINE_TRAILER_KEY,
    AGENT_NAME_TRAILER_KEY,
    AGENT_RESUME_TRAILER_KEY,
)


def trailers_for_identity(identity: AgentSessionIdentity) -> list[str]:
    trailers = [f"{AGENT_MACHINE_TRAILER_KEY}: {identity.machine_name}"]
    if identity.agent_name is not None:
        trailers.append(f"{AGENT_NAME_TRAILER_KEY}: {identity.agent_name}")
    resume_command = identity.resume_command()
    if resume_command is not None:
        trailers.append(f"{AGENT_RESUME_TRAILER_KEY}: {resume_command}")
    return trailers


def write_trailers_into_message_file(
    message_file_path: Path, trailers: list[str]
) -> None:
    interpret_trailers_arguments = [
        "git",
        "interpret-trailers",
        "--if-exists",
        "replace",
        "--in-place",
    ]
    for trailer in trailers:
        interpret_trailers_arguments.extend(["--trailer", trailer])
    interpret_trailers_arguments.append(str(message_file_path))
    subprocess.run(
        interpret_trailers_arguments, check=True, capture_output=True, text=True
    )


def parse_agent_provenance_trailers(commit_message: str) -> dict[str, str]:
    recorded_trailers: dict[str, str] = {}
    for message_line in commit_message.splitlines():
        trailer_key, separator, trailer_value = message_line.partition(":")
        if not separator:
            continue
        if trailer_key.strip() in AGENT_PROVENANCE_TRAILER_KEYS:
            recorded_trailers[trailer_key.strip()] = trailer_value.strip()
    return recorded_trailers
