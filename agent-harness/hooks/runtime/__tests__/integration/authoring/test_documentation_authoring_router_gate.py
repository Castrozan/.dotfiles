import pytest
from authoring_router_test_support import assert_allowed, assert_blocked

README_EDIT_TARGET = "/home/lucas.zanoni/.dotfiles/README.md"
DOCS_FILE_EDIT_TARGET = "/home/lucas.zanoni/.dotfiles/docs/architecture.md"


class TestDocumentationSkillGate:
    def test_keeps_blocking_every_edit_while_the_skill_is_unloaded(
        self, invoke_documentation_authoring_router_hook
    ):
        payload = {
            "session_id": "session-doc-persistent-block",
            "tool_name": "Edit",
            "tool_input": {"file_path": README_EDIT_TARGET},
        }

        first_result = invoke_documentation_authoring_router_hook(payload)
        second_result = invoke_documentation_authoring_router_hook(payload)

        assert_blocked(first_result)
        assert_blocked(second_result)

    def test_opens_the_gate_after_the_docs_skill_is_recorded(
        self,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        edit_payload = {
            "session_id": "session-doc-gate-open",
            "tool_name": "Edit",
            "tool_input": {"file_path": README_EDIT_TARGET},
        }

        blocked_before = invoke_documentation_authoring_router_hook(edit_payload)
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-gate-open",
                "tool_name": "Skill",
                "tool_input": {"skill": "docs"},
            }
        )
        allowed_after = invoke_documentation_authoring_router_hook(edit_payload)

        assert_blocked(blocked_before)
        assert_allowed(allowed_after)

    def test_gate_opens_for_every_documentation_file_in_the_session(
        self,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-wide-gate",
                "tool_name": "Skill",
                "tool_input": {"skill": "docs"},
            }
        )

        readme_result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-wide-gate",
                "tool_name": "Edit",
                "tool_input": {"file_path": README_EDIT_TARGET},
            }
        )
        docs_dir_result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-wide-gate",
                "tool_name": "Write",
                "tool_input": {"file_path": DOCS_FILE_EDIT_TARGET},
            }
        )

        assert_allowed(readme_result)
        assert_allowed(docs_dir_result)

    def test_gate_is_scoped_to_the_recording_session(
        self,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-with-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": "docs"},
            }
        )

        other_session_result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-without-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": README_EDIT_TARGET},
            }
        )

        assert_blocked(other_session_result)

    def test_unrelated_skill_invocation_does_not_open_the_gate(
        self,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-unrelated-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": "nix"},
            }
        )

        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-unrelated-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": README_EDIT_TARGET},
            }
        )

        assert_blocked(result)

    @pytest.mark.parametrize(
        "skill_name,expected_blocked",
        [
            ("plugin:docs", False),
            ("marketplace:docs", False),
            ("plugin:not-docs", True),
            ("docs-helper", True),
            ("docs:extras", True),
        ],
    )
    def test_only_the_docs_skill_or_its_namespaced_form_opens_the_gate(
        self,
        skill_name,
        expected_blocked,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-namespaced-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": skill_name},
            }
        )

        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-namespaced-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": README_EDIT_TARGET},
            }
        )

        if expected_blocked:
            assert_blocked(result)
        else:
            assert_allowed(result)

    def test_instructions_skill_invocation_does_not_open_the_docs_gate(
        self,
        invoke_documentation_authoring_router_hook,
        invoke_record_skill_invocation_hook,
    ):
        invoke_record_skill_invocation_hook(
            {
                "session_id": "session-doc-instructions-skill",
                "tool_name": "Skill",
                "tool_input": {"skill": "instructions"},
            }
        )

        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-doc-instructions-skill",
                "tool_name": "Edit",
                "tool_input": {"file_path": README_EDIT_TARGET},
            }
        )

        assert_blocked(result)
