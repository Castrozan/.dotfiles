import pytest


class TestBashDirenvBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "direnv allow",
            "direnv hook fish",
            "direnv exec . make",
            "direnv reload",
            "direnv status",
            'eval "$(direnv hook bash)"',
            "cd project && direnv allow",
            "true; direnv allow",
        ],
    )
    def test_blocks_direnv_invocations(
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
        assert "direnv" in message.lower()
        assert "devenv" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "git commit -m 'remove direnv from project'",
            "echo 'direnv was here'",
            "grep direnv ~/.config/fish/config.fish",
        ],
    )
    def test_does_not_falsely_block_direnv_mentions(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
