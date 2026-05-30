import pytest


class TestAgentDirectedInstructionFilesAreRoutedToAuthoringStandards:
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
            "/home/lucas.zanoni/.dotfiles/agents/skills/instructions/SKILL.md",
            "/home/lucas.zanoni/.dotfiles/agents/skills/review/docs.md",
            "some/repo/skills/nested/deeply/notes.md",
        ],
    )
    def test_blocks_first_edit_to_agent_directed_file(
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
        assert result.returncode == 2
        assert "Skill(skill='instructions')" in result.stderr
        assert "docs.md" in result.stderr

    @pytest.mark.parametrize(
        "file_path",
        [
            "/home/lucas.zanoni/.dotfiles/home/base/claude/hook-config.nix",
            "/tmp/scratch.txt",
            "/home/lucas.zanoni/.dotfiles/README.md",
            "docs/architecture.md",
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
        assert result.returncode == 0
        assert result.stdout == ""

    def test_blocks_only_the_first_edit_to_a_file_per_session(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        payload = {
            "session_id": "session-debounce",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
        }

        first_result = invoke_agent_instruction_file_authoring_router_hook(payload)
        second_result = invoke_agent_instruction_file_authoring_router_hook(payload)

        assert first_result.returncode == 2
        assert second_result.returncode == 0
        assert second_result.stdout == ""

    def test_nudges_each_distinct_file_independently_within_a_session(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        claude_md_result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-distinct",
                "tool_name": "Edit",
                "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
            }
        )
        skill_md_result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-distinct",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/home/lucas.zanoni/.dotfiles/agents/skills/nix/SKILL.md"
                },
            }
        )

        assert claude_md_result.returncode == 2
        assert skill_md_result.returncode == 2

    def test_ignores_input_without_a_file_path(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        result = invoke_agent_instruction_file_authoring_router_hook(
            {"session_id": "session-empty", "tool_name": "Edit", "tool_input": {}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
