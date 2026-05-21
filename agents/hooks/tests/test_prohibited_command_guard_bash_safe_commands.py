import pytest


class TestBashSafeCommands:
    @pytest.mark.parametrize(
        "command",
        [
            "ls -la",
            "git status",
            "git log --oneline -10",
            "git push origin main",
            "git commit -m 'fix: thing'",
            "git commit -m 'msg' --no-verify",
            "git push --no-verify origin main",
            "echo hello",
            "python3 -m pytest",
            "python3 -m json.tool",
            "mkdir -p /tmp/somewhere",
            "nix flake check",
            "devenv shell",
            "devenv shell -- make build",
            "pip install requests",
            "uv sync",
            "python3 -m venv .venv",
            "virtualenv .venv",
            "pipx install black",
            "poetry install",
        ],
    )
    def test_allows_safe_commands(self, command, invoke_prohibited_command_guard_hook):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
