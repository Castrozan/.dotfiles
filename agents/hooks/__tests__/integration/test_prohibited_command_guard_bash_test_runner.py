import pytest


class TestBashTestRunnerBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "__tests__/run.sh",
            "./__tests__/run.sh --quick",
            "~/.dotfiles/__tests__/run.sh --nix",
            "/tmp/dotfiles/__tests__/run.sh --all",
            "cd dotfiles && __tests__/run.sh --ci",
            "env FOO=1 ./__tests__/run.sh --quick",
            "bash __tests__/run.sh --quick",
            "bash -lc './__tests__/run.sh --quick'",
            "bash -lc 'cd dotfiles && ./__tests__/run.sh --quick'",
            "source ./__tests__/run.sh",
            "./__test[s]__/run.sh --quick",
            "./__te?ts__/run.sh --quick",
            "./__tes[t]s__/run.sh --quick",
            "./__t[e]sts__/run.sh --quick",
            "./*tests__/run.sh --quick",
            "./__test*/run.sh --quick",
            "./__tests__/'run.sh' --quick",
            r"./__tests__/run\.sh --quick",
            'name=run.sh; ./__tests__/"$name" --quick',
            "./__tests__/$'run.sh' --quick",
            './__tests__/$"run.sh" --quick',
            "./__tests__/ru\\\nn.sh --quick",
            "bash -lc \"$(printf './__tests__/%s --quick' run.sh)\"",
            "directory=__tests__; runner=run.sh; ./$directory/$runner --quick",
            "directory=__tests__; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
            "directory='__tests__'; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
            "bash -lc \"$(printf './__tests__/%s%s --quick' run .sh)\"",
            "cd __tests__; ./`printf run`.`printf sh` --quick",
            'bash -O extglob -c "./__test@(s)__/run.sh --quick"',
            "grep -R '__tests__/run.sh' agents",
            "echo '__tests__/run.sh is reserved for CI'",
            "cat __tests__/run.sh",
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
        assert "__tests__/run.sh" in message
        assert "ci" in message.lower()

    def test_allows_targeted_test_file_command(
        self, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "pytest agents/hooks/__tests__/unit/test_codex_prohibited_command_guard.py"
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
                    "command": 'pytest agents/hooks/__tests__/unit/test_codex_prohibited_command_guard.py -k "$TEST_FILTER"'
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
                    "command": 'TEST_FILTER="$(printf targeted)"; pytest agents/hooks/__tests__/unit/test_codex_prohibited_command_guard.py -k "$TEST_FILTER"'
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
                    "command": 'cd __tests__; pytest ../agents/hooks/__tests__/unit/test_codex_prohibited_command_guard.py -k "$(printf targeted)"'
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestCiOwnedSuiteRunBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "pytest agents/__tests__/unit",
            "pytest agents/__tests__/unit -q",
            "pytest agents/__tests__/unit/",
            "pytest agents/__tests__/unit//",
            "pytest agents/__tests__/unit && echo done",
            "pytest agents/__tests__/integration",
            "pytest agents/hooks/__tests__/unit",
            "pytest home/base/system/__tests__/integration",
            "pytest agents/__tests__",
            "pytest agents/__tests__/",
            "pytest agents/__tests__ -q",
            "pytest agents",
            "pytest agents/",
            "pytest ./agents",
            "pytest ./agents -q",
            "pytest agents -q",
            "pytest agents --tb=short",
            "pytest .",
            "pytest ./",
            "pytest . -q",
            "pytest",
            "pytest -q",
            "pytest -n auto",
            "pytest -q -n auto",
            "python3 -m pytest agents/__tests__/unit",
            "python3 -m pytest agents/__tests__/unit/",
            "cd __tests__; pytest ../agents/__tests__/unit",
            "pytest agents/__tests__/unit/*",
            "pytest agents/__tests__/unit/**",
            "make test",
            "make test && echo done",
            "make -j4 test",
            "make -j 4 test",
            "nix flake check",
            "nix flake check --keep-going --print-build-logs --show-trace",
            "sudo nix flake check",
        ],
    )
    def test_blocks_ci_owned_suite_runs(
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
        assert "BLOCKED" in message
        assert "ci" in message.lower()

    def test_globbed_tier_run_reports_pytest_reason(
        self,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "pytest agents/__tests__/unit/*"},
            }
        )
        assert result.returncode == 0
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "run.sh" not in message
        assert "pytest" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "pytest agents/__tests__/unit/test_run_evals_baseline.py",
            "pytest agents/__tests__/unit/test_run_evals_baseline.py -k freshness",
            "pytest agents/__tests__/e2e/",
            "pytest agents/__tests__/e2e -q",
            "pytest agents/__tests__/integration/run-integration-tests.py",
            "pytest agents/hooks/__tests__/e2e/test_something.py",
            "python3 agents/__tests__/run-evals.py",
            "python3 agents/__tests__/run-evals.py --check-baseline",
            "python3 agents/__tests__/integration/run-integration-tests.py",
            "python3 agents/__tests__/e2e/run-e2e-tests.py",
            "python3 agents/__tests__/run-coached-session-test.py",
            "make test-modules",
            "make -j4 test-modules",
            "nix eval .#nixosConfigurations.chise.config.system.build.toplevel",
            "nix flake check --help",
            "nix flake check --version",
            "pytest --version",
            "pytest --help",
            "pytest --fixtures",
            "bats tests/nix-modules/home-manager.bats",
        ],
    )
    def test_allows_targeted_and_local_only_test_runs(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
