import pytest
from authoring_router_test_support import (
    assert_allowed,
    assert_blocked,
    permission_reason,
)


class TestInstructionFileClassification:
    @pytest.mark.parametrize(
        "tool_name",
        ["Write", "Edit"],
    )
    @pytest.mark.parametrize(
        "file_path",
        [
            "/home/lucas.zanoni/.dotfiles/CLAUDE.md",
            "/home/lucas.zanoni/.claude/CLAUDE.md",
            "project/AGENTS.md",
            "/home/lucas.zanoni/.dotfiles/agent-harness/agent-instructions/skills/instructions/SKILL.md",
            "/home/lucas.zanoni/.dotfiles/agent-harness/agent-instructions/skills/docs/SKILL.md",
            "some/repo/skills/nested/deeply/notes.md",
        ],
    )
    def test_blocks_edit_to_agent_directed_file_until_skill_loaded(
        self,
        tool_name,
        file_path,
        invoke_agent_instruction_file_authoring_router_hook,
    ):
        result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-block",
                "tool_name": tool_name,
                "tool_input": {"file_path": file_path},
            }
        )
        assert_blocked(result)
        assert "Skill(skill='instructions')" in permission_reason(result)
        assert "Skill(skill='docs')" in permission_reason(result)

    @pytest.mark.parametrize(
        "file_path",
        [
            "/home/lucas.zanoni/.dotfiles/home/base/claude/hook-config.nix",
            "/tmp/scratch.txt",
        ],
    )
    def test_allows_files_that_do_not_instruct_an_agent(
        self, file_path, invoke_agent_instruction_file_authoring_router_hook
    ):
        result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-allow",
                "tool_name": "Edit",
                "tool_input": {"file_path": file_path},
            }
        )
        assert_allowed(result)

    def test_ignores_input_without_a_file_path(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        result = invoke_agent_instruction_file_authoring_router_hook(
            {"session_id": "session-empty", "tool_name": "Edit", "tool_input": {}}
        )
        assert_allowed(result)
