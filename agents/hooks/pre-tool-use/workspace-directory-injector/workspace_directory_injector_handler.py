from __future__ import annotations

import shlex
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402

WORKSPACE_STATE_FILE = Path("/tmp/claude-code-workspace-cwd")


def read_target_workspace_directory():
    if not WORKSPACE_STATE_FILE.exists():
        return None
    content = WORKSPACE_STATE_FILE.read_text().strip()
    if not content:
        return None
    target = Path(content).expanduser()
    if not target.is_dir():
        return None
    return str(target.resolve())


def build_workspace_environment_prefix(workspace_directory):
    quoted_directory = shlex.quote(workspace_directory)
    return (
        f"cd {quoted_directory}"
        ' && { eval "$(direnv export bash 2>/dev/null)" 2>/dev/null || true; }'
    )


def handle(hook_input):
    target_directory = read_target_workspace_directory()
    if not target_directory:
        return None
    original_command = hook_input.get("tool_input", {}).get("command", "")
    if not original_command:
        return None
    workspace_prefix = build_workspace_environment_prefix(target_directory)
    modified_command = f"{workspace_prefix} && {original_command}"
    return HandlerResult(decision="allow", updated_input={"command": modified_command})
