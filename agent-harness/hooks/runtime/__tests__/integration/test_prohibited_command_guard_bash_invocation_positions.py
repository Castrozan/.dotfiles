import pytest


class TestBashGitAddInvocationPositions:
    @pytest.mark.parametrize(
        "command",
        [
            "   git add -A",
            "\tgit add -A",
            "echo one\ngit add -A",
            "sudo git add -A",
            "$(git add -A)",
            "`git add -A`",
            "if true; then git add -A; fi",
            "for f in a; do git add -A; done",
            "nohup git add -A",
            "env FOO=1 git add -A",
            "echo hi; git add -A",
            "cd /tmp && git add -A",
            "true | git add -A",
            "git add -A",
        ],
    )
    def test_blocks_git_add_all_at_every_command_invocation_position(
        self,
        command,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "git add" in message
        assert "prohibited" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "git add specific-file.txt",
            "echo 'git add -A is prohibited here'",
            "grep -r 'git add -A' docs/",
            "digit add -A",
        ],
    )
    def test_allows_commands_that_only_mention_the_pattern(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
