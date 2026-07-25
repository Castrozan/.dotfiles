import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import find_hook_module_path, run_hook_subprocess

BLOCKED_SKILL_INVOCATION_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "blocked-skill-invocation-guard"
)


def invoke_blocked_skill_invocation_guard(payload):
    return run_hook_subprocess(
        BLOCKED_SKILL_INVOCATION_GUARD_HOOK_SCRIPT_PATH, json.dumps(payload)
    )


def test_blocks_claude_api_skill_invocation():
    result = invoke_blocked_skill_invocation_guard(
        {"tool_name": "Skill", "tool_input": {"skill": "claude-api"}}
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "claude-api" in blocked["systemMessage"]


def test_blocks_plugin_prefixed_claude_api_skill_invocation():
    result = invoke_blocked_skill_invocation_guard(
        {"tool_name": "Skill", "tool_input": {"skill": "plugin:claude-api"}}
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_allows_a_different_skill_invocation():
    result = invoke_blocked_skill_invocation_guard(
        {"tool_name": "Skill", "tool_input": {"skill": "nix"}}
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_ignores_non_skill_tool_calls():
    result = invoke_blocked_skill_invocation_guard(
        {"tool_name": "Bash", "tool_input": {"command": "echo claude-api"}}
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_ignores_malformed_stdin():
    result = run_hook_subprocess(
        BLOCKED_SKILL_INVOCATION_GUARD_HOOK_SCRIPT_PATH, "not json at all"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
