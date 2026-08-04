from __future__ import annotations

import os
import shlex
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from hook_dispatch import HandlerResult  # noqa: E402

WORKSPACE_STATE_FILE = "/tmp/claude-code-workspace-cwd"


def read_target_workspace_directory():
    try:
        with open(WORKSPACE_STATE_FILE) as workspace_state_file:
            recorded_directory = workspace_state_file.read().strip()
    except OSError:
        return None
    if not recorded_directory:
        return None
    target = os.path.expanduser(recorded_directory)
    if not os.path.isdir(target):
        return None
    return os.path.realpath(target)


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
