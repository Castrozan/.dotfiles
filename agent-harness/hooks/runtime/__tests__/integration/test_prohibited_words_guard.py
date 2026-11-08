import json

import pytest


def parse_system_message(stdout: str) -> str:
    return json.loads(stdout).get("systemMessage", "")


class TestFileContentsAndNames:
    def test_blocks_word_in_file_contents(self, invoke_prohibited_words_guard_hook):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/notes.md",
                    "content": "we deploy to the acme cluster",
                },
            }
        )
        assert result.returncode == 0
        assert "acme" in parse_system_message(result.stdout).lower()

    def test_blocks_word_in_file_name(self, invoke_prohibited_words_guard_hook):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/initech-config.nix",
                    "content": "clean body",
                },
            }
        )
        assert result.returncode == 0
        assert "file name" in parse_system_message(result.stdout).lower()

    def test_blocks_word_in_edit_replacement(self, invoke_prohibited_words_guard_hook):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/a.nix",
                    "old_string": "placeholder",
                    "new_string": "the acme account id",
                },
            }
        )
        assert result.returncode == 0
        assert "acme" in parse_system_message(result.stdout).lower()

    def test_allows_edit_that_removes_the_word(
        self, invoke_prohibited_words_guard_hook
    ):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/a.nix",
                    "old_string": "the acme account",
                    "new_string": "the work account",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_clean_write(self, invoke_prohibited_words_guard_hook):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/a.nix",
                    "content": "nothing to see here",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestPrivateConfigExemption:
    def test_allows_word_inside_private_config_path(
        self, invoke_prohibited_words_guard_hook
    ):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/private-configuration/machines.nix",
                    "content": "acme and initech are fine here",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestPublishingCommands:
    def test_blocks_word_in_git_commit_message(
        self, invoke_prohibited_words_guard_hook
    ):
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": 'git commit -m "fix acme deploy"'},
            }
        )
        assert result.returncode == 0
        assert "acme" in parse_system_message(result.stdout).lower()

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param("grep -rn acme .", id="non_publishing_command"),
            pytest.param(
                'git -C private-configuration commit -m "acme rename"',
                id="commit_scoped_to_private_config",
            ),
        ],
    )
    def test_allows_word_outside_public_publishing(
        self, invoke_prohibited_words_guard_hook, command
    ):
        result = invoke_prohibited_words_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestMachineAllowedWords:
    def test_allows_word_listed_in_machine_allowed_env(
        self, invoke_prohibited_words_guard_hook, monkeypatch
    ):
        monkeypatch.setenv("PROHIBITED_WORDS_ALLOWED", "acme")
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/notes.md",
                    "content": "we deploy to the acme cluster",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_still_blocks_other_words_when_one_is_allowed(
        self, invoke_prohibited_words_guard_hook, monkeypatch
    ):
        monkeypatch.setenv("PROHIBITED_WORDS_ALLOWED", "acme")
        result = invoke_prohibited_words_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/notes.md",
                    "content": "initech runs here",
                },
            }
        )
        assert result.returncode == 0
        assert "initech" in parse_system_message(result.stdout).lower()


class TestWordlistAbsent:
    def test_no_op_when_wordlist_missing(
        self, invoke_prohibited_words_guard_hook_without_wordlist
    ):
        result = invoke_prohibited_words_guard_hook_without_wordlist(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/Users/x/.dotfiles/a.nix",
                    "content": "acme initech everywhere",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""
