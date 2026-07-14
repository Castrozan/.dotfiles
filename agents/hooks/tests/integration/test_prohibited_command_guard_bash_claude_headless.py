import pytest


class TestBashHeadlessClaudeBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "claude -p",
            'claude -p "summarize this"',
            "claude --print",
            'claude --print "do the thing"',
            "claude --model claude-opus-4-8 -p 'x'",
            "cd project && claude -p 'hi'",
            "true; claude --print",
        ],
    )
    def test_blocks_headless_claude_invocations(
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
        assert "claude" in message.lower()
        assert "interactive" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            'CLAUDE_HEADLESS_SANCTIONED=1 claude -p "sanctioned one-off"',
            "CLAUDE_HEADLESS_SANCTIONED=1 claude --print",
        ],
    )
    def test_sanctioned_override_allows_headless_claude(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    @pytest.mark.parametrize(
        "command",
        [
            "claude",
            "claude --resume",
            "claude --version",
            "claude mcp list",
            "claude-workspace",
            "claude-update-version",
            "cla",
            "nix build .#thing --print-build-logs",
            'echo "drive claude interactively instead"',
            "grep -p claude config.fish",
        ],
    )
    def test_does_not_falsely_block_non_headless_claude(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
