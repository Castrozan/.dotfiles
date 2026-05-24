from pathlib import Path

import memory_recall


class TestEncodeCwdAsClaudeProjectDirectory:
    def test_replaces_slashes_with_dashes(self):
        result = memory_recall.encode_cwd_as_claude_project_directory(
            Path("/Users/lucas/dotfiles")
        )
        assert result == "-Users-lucas-dotfiles"

    def test_replaces_dots_with_dashes(self):
        result = memory_recall.encode_cwd_as_claude_project_directory(
            Path("/Users/lucas/.dotfiles")
        )
        assert result == "-Users-lucas--dotfiles"

    def test_handles_workspace_with_dots_and_dashes(self):
        result = memory_recall.encode_cwd_as_claude_project_directory(
            Path("/Users/lucas.zanoni/.claude-discord-agents/silver")
        )
        assert result == "-Users-lucas-zanoni--claude-discord-agents-silver"
