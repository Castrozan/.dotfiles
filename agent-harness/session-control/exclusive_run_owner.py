import json
import os
import pwd
import subprocess
import sys

from agent_session.harness import find_agent_session, session_identifier_from_command

OWNER_ENVIRONMENT_VARIABLE = "DOTFILES_EXCLUSIVE_RUN_OWNER"
SESSION_ENVIRONMENT_VARIABLES = (
    ("CODEX_THREAD_ID", "codex"),
    ("CODEX_SESSION_ID", "codex"),
    ("CLAUDE_CODE_SESSION_ID", "claude"),
    ("OPENCODE_SESSION_ID", "opencode"),
)
OWNER_FIELDS = (
    "owner_type",
    "owner_user",
    "agent_name",
    "agent_harness",
    "agent_session",
    "herdr_pane",
)


def single_line(value):
    if not isinstance(value, str):
        return ""
    return "".join(character for character in value if character.isprintable())[:256]


def decoded_owner(encoded_owner):
    if not encoded_owner or len(encoded_owner) > 4096:
        return None
    try:
        owner = json.loads(encoded_owner)
    except ValueError:
        return None
    return owner if isinstance(owner, dict) else None


def inherited_owner(environment):
    owner = decoded_owner(environment.get(OWNER_ENVIRONMENT_VARIABLE, ""))
    if owner is None:
        return None
    if owner.get("owner_type") not in (
        "agent",
        "non-agent",
        "unknown",
    ):
        return None
    return {name: single_line(owner.get(name)) for name in OWNER_FIELDS}


def environment_harness_session(environment):
    for variable, harness in SESSION_ENVIRONMENT_VARIABLES:
        if session := single_line(environment.get(variable)):
            return harness, session
    for variable, harness in (
        ("PI_UNWRAPPED_BINARY", "pi"),
        ("HERMES_AGENT_BINARY", "hermes"),
    ):
        if environment.get(variable):
            return harness, ""
    return "", ""


def harness_session(environment, process_identifier):
    harness, session = environment_harness_session(environment)
    if harness:
        return harness, session
    try:
        process = find_agent_session(process_identifier)
    except OSError:
        return "unknown", ""
    if process is None:
        return "", ""
    _, harness, command = process
    return harness, session_identifier_from_command(harness, command) or ""


def servant_name(session_identifier):
    if not session_identifier:
        return ""
    try:
        result = subprocess.run(
            ["servant-name", session_identifier],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return single_line(result.stdout.strip()) if result.returncode == 0 else ""


def run_owner_type(harness, agent_name):
    if agent_name:
        return "agent"
    if harness == "unknown":
        return "unknown"
    return "agent" if harness else "non-agent"


def resolve_run_owner(environment, process_identifier):
    if owner := inherited_owner(environment):
        return owner
    harness, session = harness_session(environment, process_identifier)
    agent_name = single_line(environment.get("CLAWDE_AGENT_NAME"))
    return {
        "owner_type": run_owner_type(harness, agent_name),
        "owner_user": pwd.getpwuid(os.getuid()).pw_name,
        "agent_name": agent_name or servant_name(session),
        "agent_harness": harness,
        "agent_session": single_line(session),
        "herdr_pane": single_line(environment.get("HERDR_PANE_ID")),
    }


if __name__ == "__main__":
    print(json.dumps(resolve_run_owner(os.environ, int(sys.argv[1]))))
