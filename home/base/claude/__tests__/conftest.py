import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

WORKSPACE_LAUNCHER_SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "skill-injection"
    / "scripts"
    / "launch-claude-workspace-session"
)


@pytest.fixture(scope="session")
def workspace_launcher_module():
    script_loader = importlib.machinery.SourceFileLoader(
        "launch_claude_workspace_session", str(WORKSPACE_LAUNCHER_SCRIPT_PATH)
    )
    module_specification = importlib.util.spec_from_loader(
        "launch_claude_workspace_session", script_loader
    )
    loaded_workspace_launcher_module = importlib.util.module_from_spec(
        module_specification
    )
    module_specification.loader.exec_module(loaded_workspace_launcher_module)
    return loaded_workspace_launcher_module
