from pathlib import Path

import memory_write


class TestEncodeCwdAsClaudeProjectDirectory:
    def test_replaces_slashes_with_dashes(self):
        result = memory_write.encode_cwd_as_claude_project_directory(
            Path("/Users/lucas/dotfiles")
        )
        assert result == "-Users-lucas-dotfiles"

    def test_replaces_dots_with_dashes(self):
        result = memory_write.encode_cwd_as_claude_project_directory(
            Path("/Users/lucas/.dotfiles")
        )
        assert result == "-Users-lucas--dotfiles"

    def test_matches_recall_hook_encoding(self):
        absolute_workspace = Path("/Users/lucas.zanoni/.claude-discord-agents/silver")
        assert (
            memory_write.encode_cwd_as_claude_project_directory(absolute_workspace)
            == "-Users-lucas-zanoni--claude-discord-agents-silver"
        )
