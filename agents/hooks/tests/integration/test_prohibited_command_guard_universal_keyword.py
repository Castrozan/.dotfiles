import pytest


PROHIBITED_KEYWORD = "openclaw"


class TestUniversalKeywordBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            f"echo {PROHIBITED_KEYWORD}",
            f"{PROHIBITED_KEYWORD} --version",
            f"cat /tmp/{PROHIBITED_KEYWORD}.log",
            f"true; {PROHIBITED_KEYWORD.upper()} run",
            f"./bin/{PROHIBITED_KEYWORD}d start",
        ],
    )
    def test_blocks_bash_commands_mentioning_keyword(
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
        assert PROHIBITED_KEYWORD in message.lower()

    @pytest.mark.parametrize(
        "tool_name,tool_input",
        [
            ("Write", {"file_path": f"/tmp/{PROHIBITED_KEYWORD}-config.json"}),
            (
                "Write",
                {
                    "file_path": "/tmp/safe.txt",
                    "content": f"line1\n{PROHIBITED_KEYWORD}\nline3",
                },
            ),
            (
                "Edit",
                {
                    "file_path": "/tmp/safe.txt",
                    "old_string": "foo",
                    "new_string": f"contains-{PROHIBITED_KEYWORD}-here",
                },
            ),
            (
                "Edit",
                {
                    "file_path": "/tmp/safe.txt",
                    "old_string": f"{PROHIBITED_KEYWORD}_legacy",
                    "new_string": "replacement",
                },
            ),
            (
                "NotebookEdit",
                {
                    "notebook_path": "/tmp/nb.ipynb",
                    "new_source": f"print('{PROHIBITED_KEYWORD}')",
                },
            ),
        ],
    )
    def test_blocks_file_tools_mentioning_keyword(
        self,
        tool_name,
        tool_input,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": tool_name, "tool_input": tool_input}
        )
        assert result.returncode == 2
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert PROHIBITED_KEYWORD in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "echo hello world",
            "git status",
            "ls -la",
        ],
    )
    def test_does_not_block_unrelated_bash_commands(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
