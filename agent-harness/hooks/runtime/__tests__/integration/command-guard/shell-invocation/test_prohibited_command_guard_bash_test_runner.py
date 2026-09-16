import pytest


class TestBashTestRunnerBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "repository/verification/run.sh",
            "./repository/verification/run.sh --quick",
            "~/.dotfiles/repository/verification/run.sh --nix",
            "/tmp/dotfiles/repository/verification/run.sh --all",
            "cd dotfiles && repository/verification/run.sh --ci",
            "env FOO=1 ./repository/verification/run.sh --quick",
            "bash repository/verification/run.sh --quick",
            "bash -lc './repository/verification/run.sh --quick'",
            "bash -lc 'cd dotfiles && ./repository/verification/run.sh --quick'",
            "source ./repository/verification/run.sh",
            "./repository/verification/'run.sh' --quick",
            r"./repository/verification/run\.sh --quick",
            'name=run.sh; ./repository/verification/"$name" --quick',
            "./repository/verification/$'run.sh' --quick",
            './repository/verification/$"run.sh" --quick',
            "./repository/verification/ru\\\nn.sh --quick",
            "bash -lc \"$(printf './repository/verification/%s --quick' run.sh)\"",
            "directory=repository/verification; runner=run.sh; ./$directory/$runner --quick",
            "directory=repository/verification; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
            "directory='repository/verification'; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
            "bash -lc \"$(printf './repository/verification/%s%s --quick' run .sh)\"",
            "cd repository/verification; ./`printf run`.`printf sh` --quick",
        ],
    )
    def test_blocks_test_runner_invocations(
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
        assert "repository/verification/run.sh" in message
        assert "ci" in message.lower()

    def test_allows_targeted_test_file_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "pytest agent-harness/hooks/runtime/__tests__/unit/test_codex_prohibited_command_guard.py"
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_targeted_test_file_command_with_filter(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'pytest agent-harness/hooks/runtime/__tests__/unit/test_codex_prohibited_command_guard.py -k "$TEST_FILTER"'
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_non_test_run_script_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "scripts/contests/run.sh"},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_fixture_run_script_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "scripts/__fixtures__/run.sh"},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_fixture_run_script_command_after_directory_change(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "cd __tests__; ../scripts/__fixtures__/run.sh"
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_non_test_double_underscore_run_script_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "scripts/__tools__/run.sh"},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_non_testimonials_run_script_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "scripts/__testimonials__/run.sh"},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_targeted_test_file_command_with_constructed_filter(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'TEST_FILTER="$(printf targeted)"; pytest agent-harness/hooks/runtime/__tests__/unit/test_codex_prohibited_command_guard.py -k "$TEST_FILTER"'
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_targeted_test_file_command_after_directory_change(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'cd __tests__; pytest ../agent-harness/hooks/runtime/__tests__/unit/test_codex_prohibited_command_guard.py -k "$(printf targeted)"'
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""
