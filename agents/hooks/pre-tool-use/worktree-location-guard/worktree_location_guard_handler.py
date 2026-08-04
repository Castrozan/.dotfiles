from __future__ import annotations

import re
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
from shell_command_invocation_position import (  # noqa: E402
    COMMAND_INVOCATION_POSITION_PREFIX,
)

OUTSIDE_REPOSITORY_OVERRIDE_SENTINEL = "WORKTREE_OUTSIDE_REPOSITORY_SANCTIONED=1"
CANONICAL_WORKTREE_DIRECTORY = ".worktrees"
BUILT_IN_WORKTREE_DIRECTORY = ".claude/worktrees"
ACCEPTED_WORKTREE_DIRECTORIES = (
    CANONICAL_WORKTREE_DIRECTORY,
    BUILT_IN_WORKTREE_DIRECTORY,
)
WORKTREE_CREATION_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}git\b[^;&|\n]*?\bworktree\s+add\b"
)
FLAGS_TAKING_A_SEPARATE_VALUE = ("-b", "-B", "--reason", "--track")
WORKTREE_LOCATION_REFERENCE_FILE_PATH = "~/.claude/hooks/worktree-location.md"


def worktree_creation_segments(command: str):
    for segment in re.split(r"[;&|\n]+", command):
        if re.search(WORKTREE_CREATION_PATTERN, f"\n{segment}"):
            yield segment


def destination_argument_of(segment: str):
    try:
        argument_vector = shlex.split(segment, comments=True)
    except ValueError:
        return None
    if "add" not in argument_vector:
        return None
    remaining = argument_vector[argument_vector.index("add") + 1 :]
    while remaining:
        candidate = remaining[0]
        if candidate in FLAGS_TAKING_A_SEPARATE_VALUE:
            remaining = remaining[2:]
            continue
        if candidate.startswith("-"):
            remaining = remaining[1:]
            continue
        return candidate
    return None


def destination_is_inside_a_repository_worktree_directory(destination: str) -> bool:
    components = [
        component
        for component in destination.replace("\\", "/").split("/")
        if component not in ("", ".")
    ]
    if ".." in components:
        return False
    for accepted in ACCEPTED_WORKTREE_DIRECTORIES:
        accepted_components = accepted.split("/")
        span = len(accepted_components)
        if any(
            components[start : start + span] == accepted_components
            for start in range(len(components) - span)
        ):
            return True
    return False


def build_denial_reason(destination: str) -> str:
    return (
        f"BLOCKED (Bash): 'git worktree add {destination}' puts a worktree outside "
        f"the repository. Worktrees live under {CANONICAL_WORKTREE_DIRECTORY}/ "
        f"inside the repo; read {WORKTREE_LOCATION_REFERENCE_FILE_PATH} for the "
        f"accepted paths and the override."
    )


def handle(hook_input):
    if hook_input.get("tool_name", "") != "Bash":
        return None
    command = (hook_input.get("tool_input", {}) or {}).get("command", "") or ""
    if OUTSIDE_REPOSITORY_OVERRIDE_SENTINEL in command:
        return None
    for segment in worktree_creation_segments(command):
        destination = destination_argument_of(segment)
        if destination is None:
            continue
        if destination_is_inside_a_repository_worktree_directory(destination):
            continue
        reason = build_denial_reason(destination)
        return HandlerResult(decision="deny", reason=reason, system_message=reason)
    return None
