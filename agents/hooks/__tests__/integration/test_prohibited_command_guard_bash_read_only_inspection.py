import pytest


class TestBashReadOnlyInspectionCommandsStayAllowed:
    @pytest.mark.parametrize(
        "command",
        [
            "git ls-files '*/__tests__/*'",
            "git ls-files '*/__tests__/*' | wc -l",
            "git ls-files '*/__tests__/*' | grep run",
            "git -C /Users/someone/.dotfiles ls-files '*/__tests__/*'",
            "git log --oneline -- __tests__/run.sh",
            "git grep -n 'make test' -- agents",
            "git show HEAD:__tests__/run.sh",
            "git diff -- __tests__/run.sh",
            "grep -R '__tests__/run.sh' agents",
            "grep -rn 'pytest agents/' agents/skills",
            "grep -rn 'nix flake check' agents",
            "rg 'make test' agents",
            "cat __tests__/run.sh",
            "head -20 __tests__/run.sh",
            "tail -5 __tests__/run.sh",
            "wc -l __tests__/run.sh",
            "ls -la agents/hooks/__tests__/unit",
            "tree agents/hooks/__tests__",
            "stat __tests__/run.sh",
            "echo '__tests__/run.sh is reserved for CI'",
            "command -v pytest",
            "which pytest",
        ],
    )
    def test_allows_read_only_inspection_of_ci_owned_test_surfaces(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestBashReadOnlyInspectionExemptionDoesNotLeakExecution:
    @pytest.mark.parametrize(
        "command",
        [
            "cat __tests__/run.sh | bash",
            "cat __tests__/run.sh | sh -",
            "cat __tests__/run.sh | python3",
            'bash -lc "$(cat __tests__/run.sh)"',
            'eval "$(cat __tests__/run.sh)"',
            "git ls-files '*/__tests__/*'; __tests__/run.sh",
            "grep -R x agents && ./__tests__/run.sh --quick",
            "echo starting | xargs __tests__/run.sh",
            "ls agents && pytest agents/hooks/__tests__/unit",
        ],
    )
    def test_blocks_execution_reached_through_a_read_only_segment(
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
        assert "ci" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "git add -A",
            "git ls-files; git add -A",
            "git clone https://github.com/castrozan/.dotfiles",
        ],
    )
    def test_keeps_blocking_non_test_rules_next_to_read_only_segments(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout != ""
