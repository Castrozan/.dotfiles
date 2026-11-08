import pytest


class TestBashGitAddInvocationPositions:
    @pytest.mark.parametrize(
        "command",
        [
            "git add specific-file.txt",
            "echo 'git add -A is prohibited here'",
            "grep -r 'git add -A' docs/",
            "digit add -A",
            "./release.sh git add .",
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
