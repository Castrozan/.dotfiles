import run_evals_ab
from run_evals_ab import (
    build_instruction_stripped_variant,
    outcomes_by_name,
    run_instruction_loading_experiment,
)
from run_evals_test_runner import TestResult


def _result(name, passed):
    return TestResult(
        name=name,
        passed=passed,
        duration=0.0,
        output="",
        assertions_failed=[],
    )


def test_stripping_removes_instruction_fields_without_mutating_the_original():
    config = {
        "tests": {
            "routing": [
                {
                    "name": "t1",
                    "prompt": "p",
                    "skill_path": "agents/skills/x/SKILL.md",
                    "agent": "x",
                    "system_prompt": "sp",
                    "extra_skill_paths": ["y"],
                    "no_tools": True,
                }
            ]
        }
    }

    control_test = build_instruction_stripped_variant(config)["tests"]["routing"][0]

    assert "skill_path" not in control_test
    assert "agent" not in control_test
    assert "system_prompt" not in control_test
    assert "extra_skill_paths" not in control_test
    assert control_test["prompt"] == "p"
    assert control_test["no_tools"] is True
    assert config["tests"]["routing"][0]["skill_path"] == "agents/skills/x/SKILL.md"


def test_outcomes_by_name_maps_pass_state():
    results = [_result("a", True), _result("b", False)]
    assert outcomes_by_name(results) == {"a": True, "b": False}


def test_experiment_pairs_instructed_run_against_stripped_control(monkeypatch):
    def fake_run_tests(config, category=None, max_workers_override=None):
        instructed = any(
            "skill_path" in test for tests in config["tests"].values() for test in tests
        )
        if instructed:
            return [_result("t1", True), _result("t2", True)]
        return [_result("t1", True), _result("t2", False)]

    monkeypatch.setattr(run_evals_ab, "run_tests", fake_run_tests)
    config = {
        "tests": {
            "routing": [
                {"name": "t1", "prompt": "p", "skill_path": "s"},
                {"name": "t2", "prompt": "p", "skill_path": "s"},
            ]
        }
    }

    comparison = run_instruction_loading_experiment(config)

    assert comparison["n_paired"] == 2
    assert comparison["variant_a_pass_rate"] == 1.0
    assert comparison["variant_b_pass_rate"] == 0.5
    assert comparison["a_only_wins"] == 1
    assert comparison["delta"] == 0.5
