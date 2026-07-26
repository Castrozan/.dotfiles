from __future__ import annotations

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

SKILL_INVOCATION_TOOL_NAME = "Skill"
BLOCKED_SKILL_NAMES = frozenset({"claude-api"})


def normalized_invoked_skill_name(tool_input):
    return (tool_input.get("skill", "") or "").strip().lower()


def is_blocked_skill(skill_name):
    if skill_name in BLOCKED_SKILL_NAMES:
        return True
    return any(
        skill_name.endswith(f":{blocked_name}") for blocked_name in BLOCKED_SKILL_NAMES
    )


def build_block_message(skill_name):
    return (
        f"The {skill_name!r} skill is blocked in this environment. Loading it injects "
        f"~309K tokens as a single message, which by itself crosses the auto-compact "
        f"trigger and forces an immediate lossy compaction. Do not retry the Skill call. "
        f"For Claude/Anthropic model ids, pricing, or SDK questions, use the model catalog "
        f"already in your session context and Read the one specific reference file you need "
        f"directly instead of loading the whole skill."
    )


def handle(hook_input):
    if hook_input.get("tool_name", "") != SKILL_INVOCATION_TOOL_NAME:
        return None
    tool_input = hook_input.get("tool_input", {}) or {}
    skill_name = normalized_invoked_skill_name(tool_input)
    if not is_blocked_skill(skill_name):
        return None
    block_message = build_block_message(skill_name)
    return HandlerResult(
        decision="deny", reason=block_message, system_message=block_message
    )
