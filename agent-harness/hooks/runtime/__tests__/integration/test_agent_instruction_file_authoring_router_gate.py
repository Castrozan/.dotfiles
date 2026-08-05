import pytest
from authoring_router_test_support import assert_allowed, assert_blocked

CLAUDE_MD_EDIT_TARGET = "/home/lucas.zanoni/.dotfiles/CLAUDE.md"


class TestInstructionsSkillGate:
    def test_keeps_blocking_every_edit_while_the_skill_is_unloaded(
        self, invoke_agent_instruction_file_authoring_router_hook
    ):
        payload = {
            "session_id": "session-persistent-block",
            "tool_name": "Edit",
            "tool_input": {"file_path": CLAUDE_MD_EDIT_TARGET},
        }

        first_result = invoke_agent_instruction_file_authoring_router_hook(payload)
        second_result = invoke_agent_instruction_file_authoring_router_hook(payload)

        assert_blocked(first_result)
        assert_blocked(second_result)

    def test_opens_the_gate_after_the_instructions_skill_is_recorded(
        self,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        edit_payload = {
            "session_id": "session-gate-open",
            "tool_name": "Edit",
            "tool_input": {"file_path": CLAUDE_MD_EDIT_TARGET},
        }

        blocked_before = invoke_agent_instruction_file_authoring_router_hook(
            edit_payload
        )
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-gate-open",
                "tool_name": "Skill",
                "tool_input": {"skill": "instructions"},
            }
        )
        allowed_after = invoke_agent_instruction_file_authoring_router_hook(
            edit_payload
        )

        assert_blocked(blocked_before)
        assert_allowed(allowed_after)

    def test_gate_is_scoped_to_the_recording_session(
        self,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
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
                "tool_input": {"file_path": CLAUDE_MD_EDIT_TARGET},
            }
        )

        assert_blocked(other_session_result)

    @pytest.mark.parametrize("unrelated_skill_name", ["nix", "docs"])
    def test_unrelated_skill_invocation_does_not_open_the_gate(
        self,
        unrelated_skill_name,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-unrelated-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": unrelated_skill_name},
            }
        )

        result = invoke_agent_instruction_file_authoring_router_hook(
            {
                "session_id": "session-unrelated-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": CLAUDE_MD_EDIT_TARGET},
            }
        )

        assert_blocked(result)

    @pytest.mark.parametrize(
        "skill_name,expected_blocked",
        [
            ("plugin:instructions", False),
            ("marketplace:instructions", False),
            ("plugin:not-instructions", True),
            ("instructions-helper", True),
            ("instructions:extras", True),
        ],
    )
    def test_only_the_instructions_skill_or_its_namespaced_form_opens_the_gate(
        self,
        skill_name,
        expected_blocked,
        invoke_agent_instruction_file_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
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
                "tool_input": {"file_path": CLAUDE_MD_EDIT_TARGET},
            }
        )

        if expected_blocked:
            assert_blocked(result)
        else:
            assert_allowed(result)
