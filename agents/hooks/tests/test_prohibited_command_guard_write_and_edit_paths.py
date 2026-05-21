import pytest


class TestWriteAndEditFilePathBlocking:
    @pytest.mark.parametrize(
        "tool_name",
        ["Write", "Edit", "NotebookEdit"],
    )
    @pytest.mark.parametrize(
        "file_path",
        [
            "/tmp/castrozan/.dotfiles/init.lua",
            "castrozan/.dotfiles/README.md",
            "/Users/lucas.zanoni/work/castrozan/dotfiles/x.nix",
        ],
    )
    def test_blocks_writes_under_castrozan_dotfiles(
        self,
        tool_name,
        file_path,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
        )
        assert result.returncode == 2
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "castrozan" in message.lower()

    @pytest.mark.parametrize(
        "tool_name",
        ["Write", "Edit"],
    )
    @pytest.mark.parametrize(
        "file_path",
        [
            "/Users/lucas.zanoni/.dotfiles/agents/hooks/example.py",
            "/tmp/scratch.txt",
            "README.md",
        ],
    )
    def test_allows_writes_outside_castrozan(
        self, tool_name, file_path, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_content_mentioning_prohibited_path(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/tmp/notes.md",
                    "content": "We do not write to castrozan/.dotfiles anymore.",
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""
