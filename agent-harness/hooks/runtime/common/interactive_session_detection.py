import os
import sys
from pathlib import Path

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_AGENT_NAME"

clawde_workspace_domain_directory = Path("@clawdeWorkspaceDomainDirectory@")
if not clawde_workspace_domain_directory.is_dir():
    clawde_workspace_domain_directory = (
        Path(__file__).resolve().parents[3] / "harnesses" / "clawde" / "scripts"
    )

clawde_workspace_domain_directory_path = str(clawde_workspace_domain_directory)
if clawde_workspace_domain_directory_path not in sys.path:
    sys.path.insert(0, clawde_workspace_domain_directory_path)

from clawde_workspace_paths import agents_directory  # noqa: E402


def is_session_running_inside_a_clawde_agent_workspace() -> bool:
    return agents_directory() in Path.cwd().resolve().parents


def is_clawde_background_agent_session() -> bool:
    if CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER in os.environ:
        return True
    return is_session_running_inside_a_clawde_agent_workspace()


def is_keyboard_driven_interactive_session() -> bool:
    if is_clawde_background_agent_session():
        return False
    return bool(os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE))
