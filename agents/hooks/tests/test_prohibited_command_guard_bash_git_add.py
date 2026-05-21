import pytest


class TestBashGitAddBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "git add -A",
            "git add --all",
            "git add .",
            "git add -A path/file.txt",
            "git add . && echo done",
        ],
    )
    def test_blocks_wildcard_git_add_forms(
        self,
        command,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 2
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "git add" in message
        assert "prohibited" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "git add specific-file.txt",
            "git add path/to/file.py",
            "git add agents/hooks/pre-tool-use/prohibited-command-guard.py",
        ],
    )
    def test_allows_specific_path_git_add(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
