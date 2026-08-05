import pytest


class TestBashHerdrUnpinnedAgentStartBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "herdr agent start demo --cwd /tmp -- claude",
            "herdr agent start demo --cwd /tmp --no-focus -- claude",
            "herdr agent start demo --cwd /tmp --split right -- claude --name demo",
            "cd /tmp && herdr agent start demo --cwd /tmp -- claude",
            "true; herdr agent start demo --cwd /tmp -- claude",
            "herdr agent start demo --cwd /tmp -- claude --tab foo",
            "herdr agent start demo --workspace-dir x -- claude",
            "herdr agent start demo --cwd /tmp --workspace w1 -- claude",
            "herdr agent start demo --cwd /tmp --workspace=w1 --no-focus -- claude",
            "herdr agent start demo --cwd /tmp --workspace w1 --split down -- claude",
        ],
    )
    def test_blocks_unpinned_agent_start(
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
        assert "herdr" in message.lower()
        assert "--tab" in message.lower() or "--workspace" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            'herdr agent start demo --cwd /tmp --tab "$HERDR_TAB_ID" --no-focus -- claude',
            'herdr agent start demo --cwd "$(pwd)" --tab "$HERDR_TAB_ID" --no-focus -- claude',
            "herdr agent start demo --cwd /tmp --tab w1:tA -- claude",
            "herdr agent start demo --cwd /tmp --tab=w1:tA -- claude",
            "herdr agent start demo --cwd /tmp --workspace w1 --tab w1:tA -- claude",
            "herdr tab create --workspace w1 --no-focus",
            "herdr agent wait demo --status idle",
            "herdr agent read demo --source recent",
            "herdr agent send demo 'count to 5'",
            "echo 'herdr agent start demo -- claude'",
            "grep 'herdr agent start' notes.md",
        ],
    )
    def test_does_not_block_pinned_or_other_herdr_commands(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
