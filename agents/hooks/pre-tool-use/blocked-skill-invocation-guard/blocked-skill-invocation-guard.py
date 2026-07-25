from __future__ import annotations

import json
import sys

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


def emit_denial_and_exit(skill_name):
    block_message = (
        f"The {skill_name!r} skill is blocked in this environment. Loading it injects "
        f"~309K tokens as a single message, which by itself crosses the auto-compact "
        f"trigger and forces an immediate lossy compaction. Do not retry the Skill call. "
        f"For Claude/Anthropic model ids, pricing, or SDK questions, use the model catalog "
        f"already in your session context and Read the one specific reference file you need "
        f"directly instead of loading the whole skill."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": block_message,
        },
        "systemMessage": block_message,
    }
    print(json.dumps(output))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("tool_name", "") != SKILL_INVOCATION_TOOL_NAME:
        sys.exit(0)

    tool_input = data.get("tool_input", {}) or {}
    skill_name = normalized_invoked_skill_name(tool_input)
    if not is_blocked_skill(skill_name):
        sys.exit(0)

    emit_denial_and_exit(skill_name)


if __name__ == "__main__":
    main()
