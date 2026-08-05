import pytest


class TestBashReadOnlyInspectionCommandsStayAllowed:
    @pytest.mark.parametrize(
        "command",
        [
            "git ls-files '*/__tests__/*'",
            "git ls-files '*/__tests__/*' | wc -l",
            "git ls-files '*/__tests__/*' | grep run",
            "git -C /Users/someone/.dotfiles ls-files '*/__tests__/*'",
            "git log --oneline -- repository/verification/run.sh",
            "git grep -n 'make test' -- agents",
            "git show HEAD:repository/verification/run.sh",
            "git diff -- repository/verification/run.sh",
            "grep -R 'repository/verification/run.sh' agents",
            "grep -rn 'pytest agents/' agent-harness/agent-instructions/skills",
            "grep -rn 'nix flake check' agents",
            "rg 'make test' agents",
            "cat repository/verification/run.sh",
            "head -20 repository/verification/run.sh",
            "tail -5 repository/verification/run.sh",
            "wc -l repository/verification/run.sh",
            "ls -la agent-harness/hooks/runtime/__tests__/unit",
            "tree agent-harness/hooks/runtime/__tests__",
            "stat repository/verification/run.sh",
            "echo 'repository/verification/run.sh is reserved for CI'",
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

    @pytest.mark.parametrize(
        "command",
        [
            'grep -rn "check_baseline\\|check-baseline" agents/__tests__/evals/*.py',
            "grep -c 'unit\\|integration' agent-harness/hooks/runtime/__tests__/unit/test_thing.py",
            'echo "the suite lives at repository/verification/run.sh; CI runs it" | wc -l',
            "git log --oneline -- 'agents/__tests__/*'",
            'grep -rln "pytest agents/" agents | head -5',
        ],
    )
    def test_a_separator_inside_quotes_does_not_split_the_read_only_segment(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestHeredocBodiesAreDataRatherThanCommands:
    @pytest.mark.parametrize(
        "command",
        [
            "git commit -F- -- agent-harness/hooks/runtime <<'MESSAGE'\n"
            "fix(hooks): explain the ban\n"
            "\n"
            "Running repository/verification/run.sh locally stays prohibited.\n"
            "MESSAGE",
            "gh issue create --body-file - <<'BODY'\n"
            "pytest agents/ belongs to CI.\n"
            "BODY",
            "cat <<'NOTE' > notes.md\nmake test is CI-owned.\nNOTE",
        ],
    )
    def test_a_body_the_command_only_reads_is_allowed(
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
            "bash <<'EOF'\nrepository/verification/run.sh --quick\nEOF",
            "cat <<'EOF' | bash\nrepository/verification/run.sh --quick\nEOF",
            "sudo bash <<'EOF'\nrepository/verification/run.sh\nEOF",
        ],
    )
    def test_a_body_an_interpreter_executes_is_still_blocked(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout != ""


class TestBashReadOnlyInspectionExemptionDoesNotLeakExecution:
    @pytest.mark.parametrize(
        "command",
        [
            "cat repository/verification/run.sh | bash",
            "cat repository/verification/run.sh | sh -",
            "cat repository/verification/run.sh | python3",
            'bash -lc "$(cat repository/verification/run.sh)"',
            'eval "$(cat repository/verification/run.sh)"',
            "git ls-files '*/__tests__/*'; repository/verification/run.sh",
            "grep -R x agents && ./repository/verification/run.sh --quick",
            "echo starting | xargs repository/verification/run.sh",
            "ls agents && pytest agent-harness/hooks/runtime/__tests__/unit",
            "grep -rn 'a\\|b' agents; pytest agent-harness/hooks/runtime/__tests__/unit",
            "echo 'a|b' | bash -c 'pytest agent-harness/hooks/runtime/__tests__/unit'",
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
