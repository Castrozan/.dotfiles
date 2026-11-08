import pytest


class TestCiOwnedSuiteRunBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "pytest agent-harness/quality/evaluations/__tests__/unit//",
            "pytest agent-harness/quality/evaluations/integration",
            "pytest machine-configuration/operating-system/memory-protection/__tests__/integration",
            "pytest -k 'test_name or other_name' -m slow",
            "pytest --rootdir agent-harness/hooks/runtime --ignore a.py",
            "pytest --ignore=a.py -q",
            "pytest --cov --cov-report term",
            "pytest --debug --ignore ignored.py",
            "pytest --cov --ignore ignored.py --cov-report term",
            "pytest --debug --cov --ignore ignored.py",
            "pytest --cov ignored.py",
            "pytest --debug ignored.py",
            "pytest --cov= --ignore ignored.py",
            "pytest --debug=debug.log --ignore ignored.py",
            "pytest -k a.py",
            "pytest -m a.py",
            "pytest -c pytest.ini --maxfail 1",
            "pytest -q > test-results.log",
            "pytest a.py && pytest -q",
            "py'test' -q",
            'bash -lc "pytest a.py; pytest -q"',
            'pytest -k "$(printf filter)"',
            'pytest agent-harness/hooks/runtime/__tests__/unit -k "$(printf filter)"',
            "cd __tests__; pytest ../agent-harness/quality/evaluations/__tests__/unit",
            "pytest agent-harness/quality/evaluations/__tests__/unit/*",
            "pytest agent-harness/quality/evaluations/__tests__/unit/**",
            "nix flake check --keep-going --print-build-logs --show-trace",
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
                "tool_input": {
                    "command": "pytest agent-harness/quality/evaluations/__tests__/unit/*"
                },
            }
        )
        assert result.returncode == 0
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "run.sh" not in message
        assert "pytest" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "pytest agent-harness/quality/evaluations/__tests__/unit/suites/test_adversarial_suite_is_enforced.py",
            "pytest agent-harness/quality/evaluations/__tests__/unit/suites/test_adversarial_suite_is_enforced.py -k hooks",
            "pytest -q machine-configuration/desktop/appearance/screensaver/ambient-canvas/__tests__/unit/scenes/test_ambient_canvas_media_arguments.py",
            "pytest -q agent-harness/hooks/runtime/__tests__/unit/test_example.py",
            "pytest -k 'test_name or other_name' -m slow --rootdir . -q a.py",
            "pytest a.py -q -k test_name -m slow --rootdir .",
            "pytest -q 'tests with spaces/test_example.py::test_example[param|value]'",
            "pytest -q a.py::TestExample::test_example",
            "pytest --rootdir agent-harness/hooks/runtime/__tests__/unit a.py",
            "pytest a.py -m agents",
            "pytest --ignore ignored.py -q a.py",
            "pytest --cov --cov-report term a.py",
            "pytest --debug --ignore ignored.py a.py",
            "pytest --cov --debug --ignore ignored.py a.py",
            "pytest --cov source --cov-report term a.py",
            "pytest --debug debug.log --ignore ignored.py a.py",
            "pytest --cov= --cov-report term a.py",
            "pytest --debug=debug.log --ignore ignored.py a.py",
            "pytest -q a.py --ignore ignored.py",
            "pytest --rootdir=. --maxfail=1 --tb=short -q a.py",
            "pytest -c pytest.ini -o addopts= -p no:cacheprovider -q a.py",
            "pytest -k test_name -m slow --rootdir . -- a.py",
            "pytest -q a.py && pytest -q b.py",
            "pytest -q a.py > test-results.log",
            "python -m pytest -q a.py",
            "python3 -m pytest -q a.py::test_example",
            "pytest -q --help",
            "py'test' -q a.py",
            '"pytest" -q a.py',
            'pytest -k "$(printf filter)" a.py',
            "pytest agent-harness/quality/evaluations/e2e/",
            "pytest agent-harness/quality/evaluations/e2e -q",
            "pytest agent-harness/hooks/runtime/__tests__/e2e/test_something.py",
            "dotfiles-evals run --caso git_stages_specific_files_not_all",
            "dotfiles-evals check --gravado",
            "dotfiles-evals testes",
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
