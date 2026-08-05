import pytest
from authoring_router_test_support import (
    assert_allowed,
    assert_blocked,
    permission_reason,
)


class TestDocumentationFileClassification:
    @pytest.mark.parametrize(
        "tool_name",
        ["Write", "Edit"],
    )
    @pytest.mark.parametrize(
        "file_path",
        [
            "/home/lucas.zanoni/.dotfiles/README.md",
            "/home/lucas.zanoni/.dotfiles/hosts/chise/README.md",
            "/home/lucas.zanoni/.dotfiles/home/base/claude/docs/context-management.md",
            "/home/lucas.zanoni/.dotfiles/docs/architecture.md",
            "docs/architecture.md",
            "/home/lucas.zanoni/.dotfiles/Documentation/guides/install.md",
        ],
    )
    def test_blocks_edit_to_documentation_file_until_skill_loaded(
        self,
        tool_name,
        file_path,
        invoke_documentation_authoring_router_hook,
    ):
        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-block-doc",
                "tool_name": tool_name,
                "tool_input": {"file_path": file_path},
            }
        )
        assert_blocked(result)
        assert "Skill(skill='docs')" in permission_reason(result)

    @pytest.mark.parametrize(
        "file_path",
        [
            "/home/lucas.zanoni/.dotfiles/home/base/claude/hook-config.nix",
            "/tmp/scratch.txt",
            "/home/lucas.zanoni/.dotfiles/HEARTBEAT.md",
            "/home/lucas.zanoni/.dotfiles/briefings/2026-08-02.md",
            "/home/lucas.zanoni/.dotfiles/ril/decisions/tweet-from-2026-07-25-10-16-14.md",
            "/home/lucas.zanoni/.dotfiles/agents/telemetry/dashboard/node_modules/@algolia/client-search/README.md",
            "/home/lucas.zanoni/.dotfiles/agents/telemetry/infrastructure/.terraform/providers/google/6.50.0/darwin_arm64/README.md",
            "/home/lucas.zanoni/.dotfiles/nixos/modules/network-policy.md",
        ],
    )
    def test_allows_files_that_are_not_user_facing_documentation(
        self, file_path, invoke_documentation_authoring_router_hook
    ):
        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-allow-doc",
                "tool_name": "Edit",
                "tool_input": {"file_path": file_path},
            }
        )
        assert_allowed(result)

    def test_ignores_input_without_a_file_path(
        self, invoke_documentation_authoring_router_hook
    ):
        result = invoke_documentation_authoring_router_hook(
            {"session_id": "session-empty-doc", "tool_name": "Edit", "tool_input": {}}
        )
        assert_allowed(result)

    def test_blocks_apply_patch_payload_adding_a_readme(
        self, invoke_documentation_authoring_router_hook
    ):
        result = invoke_documentation_authoring_router_hook(
            {
                "session_id": "session-apply-patch-doc",
                "tool_name": "apply_patch",
                "tool_input": {
                    "command": [
                        "apply_patch",
                        "*** Begin Patch\n*** Add File: README.md\n# title\n*** End Patch",
                    ]
                },
                "cwd": "/home/lucas.zanoni/.dotfiles",
            }
        )
        assert_blocked(result)
