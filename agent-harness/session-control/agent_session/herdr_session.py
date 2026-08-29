import json
import subprocess


def herdr_pane_agent_session_identifier(
    pane_identifier: str, harness_name: str
) -> str | None:
    try:
        completed_process = subprocess.run(
            ["herdr", "agent", "get", pane_identifier],
            capture_output=True,
            text=True,
            check=False,
        )
        agent_session = json.loads(completed_process.stdout)["result"]["agent"][
            "agent_session"
        ]
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return None
    if completed_process.returncode != 0:
        return None
    if not isinstance(agent_session, dict):
        return None
    if agent_session.get("agent") != harness_name or agent_session.get("kind") != "id":
        return None
    session_identifier = agent_session.get("value")
    if not isinstance(session_identifier, str) or not session_identifier:
        return None
    return session_identifier
