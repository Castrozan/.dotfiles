import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

blocked_skill_invocation_guard_handler = import_hyphenated_hook_module(
    "blocked_skill_invocation_guard_handler"
)


def test_blocks_claude_api_skill_invocation():
    result = blocked_skill_invocation_guard_handler.handle(
        {"tool_name": "Skill", "tool_input": {"skill": "claude-api"}}
    )
    assert result is not None
    assert result.decision == "deny"
    assert "claude-api" in result.system_message


def test_blocks_plugin_prefixed_claude_api_skill_invocation():
    result = blocked_skill_invocation_guard_handler.handle(
        {"tool_name": "Skill", "tool_input": {"skill": "plugin:claude-api"}}
    )
    assert result is not None
    assert result.decision == "deny"


def test_allows_a_different_skill_invocation():
    result = blocked_skill_invocation_guard_handler.handle(
        {"tool_name": "Skill", "tool_input": {"skill": "nix"}}
    )
    assert result is None


def test_ignores_non_skill_tool_calls():
    result = blocked_skill_invocation_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": "echo claude-api"}}
    )
    assert result is None
