import pytest


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
