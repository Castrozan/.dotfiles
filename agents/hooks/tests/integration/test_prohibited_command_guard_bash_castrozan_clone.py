import pytest


class TestBashCastrozanCloneBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "git clone https://github.com/castrozan/.dotfiles",
            "git clone git@github.com:castrozan/dotfiles.git",
            "gh repo clone castrozan/.dotfiles",
            "gh repo clone castrozan/dotfiles",
        ],
    )
    def test_blocks_castrozan_clone_variants(
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
        assert "castrozan" in message.lower()
