import pytest


class TestInstructionFileEditsAreGatedOnTheInstructionsSkill:
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

    def test_keeps_blocking_every_edit_while_the_skill_is_unloaded(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        payload = {
            "session_id": "session-persistent-block",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
        }

        first_result = invoke_agent_instruction_file_authoring_router_hook(payload)
        second_result = invoke_agent_instruction_file_authoring_router_hook(payload)

        assert first_result.returncode == 2
        assert second_result.returncode == 2

    def test_opens_the_gate_after_the_instructions_skill_is_recorded(
        self,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_instructions_skill_invocation_hook,
    ):
        edit_payload = {
            "session_id": "session-gate-open",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
        }

        blocked_before = invoke_agent_instruction_file_authoring_router_hook(
            edit_payload
        )
        invoke_record_instructions_skill_invocation_hook(
            {
                "session_id": "session-gate-open",
                "tool_name": "Skill",
                "tool_input": {"skill": "instructions"},
            }
        )
        allowed_after = invoke_agent_instruction_file_authoring_router_hook(
            edit_payload
        )

        assert blocked_before.returncode == 2
        assert allowed_after.returncode == 0
        assert allowed_after.stdout == ""

    def test_gate_is_scoped_to_the_recording_session(
        self,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_instructions_skill_invocation_hook,
    ):
        invoke_record_instructions_skill_invocation_hook(
            {
                "session_id": "session-with-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": "instructions"},
            }
        )

        other_session_result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-without-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
            }
        )

        assert other_session_result.returncode == 2

    def test_unrelated_skill_invocation_does_not_open_the_gate(
        self,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_instructions_skill_invocation_hook,
    ):
        invoke_record_instructions_skill_invocation_hook(
            {
                "session_id": "session-unrelated-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": "nix"},
            }
        )

        result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-unrelated-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
            }
        )

        assert result.returncode == 2

    @pytest.mark.parametrize(
        "skill_name,expected_returncode",
        [
            ("plugin:instructions", 0),
            ("marketplace:instructions", 0),
            ("plugin:not-instructions", 2),
            ("instructions-helper", 2),
            ("instructions:extras", 2),
        ],
    )
    def test_only_the_instructions_skill_or_its_namespaced_form_opens_the_gate(
        self,
        skill_name,
        expected_returncode,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_instructions_skill_invocation_hook,
    ):
        invoke_record_instructions_skill_invocation_hook(
            {
                "session_id": "session-namespaced-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": skill_name},
            }
        )

        result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-namespaced-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": "/home/lucas.zanoni/.dotfiles/CLAUDE.md"},
            }
        )

        assert result.returncode == expected_returncode

    def test_ignores_input_without_a_file_path(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        result = invoke_agent_instruction_file_authoring_router_hook(
            {"session_id": "session-empty", "tool_name": "Edit", "tool_input": {}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
