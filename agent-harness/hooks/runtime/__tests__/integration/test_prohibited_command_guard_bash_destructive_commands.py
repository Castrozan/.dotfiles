import json

import pytest

RESTRICTED_AGENT_NAME = "monster"
UNRESTRICTED_AGENT_NAME = "steward"

DESTRUCTIVE_COMMANDS = [
    "rm -rf /tmp/somewhere",
    "rm f.txt",
    "rmdir /tmp/somewhere",
    "sudo systemctl restart herdr",
    "sudo -n true",
    "dd if=/dev/zero of=/dev/sda",
    "mkfs.ext4 /dev/sda1",
    "mkfs /dev/sda1",
    "fdisk /dev/sda",
    "shutdown -h now",
    "reboot",
    "halt",
    "poweroff",
    "ls -la && rm -rf /tmp/somewhere",
    "echo hi; sudo reboot",
    "$(rm -rf /tmp/somewhere)",
]


def declare_agents_denied_destructive_commands(home_directory, agent_names):
    clawde_directory = home_directory / "clawde"
    clawde_directory.mkdir(parents=True, exist_ok=True)
    (clawde_directory / "agents-denied-destructive-commands.json").write_text(
        json.dumps(agent_names), encoding="utf-8"
    )


@pytest.fixture
def run_turn_of_a_denied_agent(
    tmp_path, monkeypatch, invoke_prohibited_command_guard_hook
):
    declare_agents_denied_destructive_commands(tmp_path, [RESTRICTED_AGENT_NAME])
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWDE_AGENT_NAME", RESTRICTED_AGENT_NAME)
    return invoke_prohibited_command_guard_hook


class TestDestructiveCommandsOfADeniedAgent:
    @pytest.mark.parametrize("command", DESTRUCTIVE_COMMANDS)
    def test_blocks_destructive_commands(
        self,
        command,
        run_turn_of_a_denied_agent,
        parse_prohibited_command_guard_system_message,
    ):
        result = run_turn_of_a_denied_agent(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "BLOCKED" in message
        assert "destructive system commands" in message

    @pytest.mark.parametrize(
        "command",
        [
            "ls -la",
            "git status",
            "npm rm left-pad",
            "git rm --cached f.txt",
            "echo 'rm -rf /tmp/somewhere'",
            "grep -rn reboot .",
        ],
    )
    def test_allows_commands_that_only_look_destructive(
        self, command, run_turn_of_a_denied_agent
    ):
        result = run_turn_of_a_denied_agent(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestDestructiveCommandsOfEveryoneElse:
    def test_allows_an_agent_that_is_not_denied(
        self, tmp_path, monkeypatch, invoke_prohibited_command_guard_hook
    ):
        declare_agents_denied_destructive_commands(tmp_path, [RESTRICTED_AGENT_NAME])
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("CLAWDE_AGENT_NAME", UNRESTRICTED_AGENT_NAME)
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/somewhere"}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_a_human_session_carrying_no_agent_name(
        self, tmp_path, monkeypatch, invoke_prohibited_command_guard_hook
    ):
        declare_agents_denied_destructive_commands(tmp_path, [RESTRICTED_AGENT_NAME])
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/somewhere"}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_a_denied_agent_when_the_declaration_is_missing(
        self, tmp_path, monkeypatch, invoke_prohibited_command_guard_hook
    ):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("CLAWDE_AGENT_NAME", RESTRICTED_AGENT_NAME)
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/somewhere"}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
