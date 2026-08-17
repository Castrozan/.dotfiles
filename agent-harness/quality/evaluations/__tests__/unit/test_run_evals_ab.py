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
                    "skill_path": "agent-harness/agent-instructions/skills/x/SKILL.md",
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
    assert (
        config["tests"]["routing"][0]["skill_path"]
        == "agent-harness/agent-instructions/skills/x/SKILL.md"
    )


def test_outcomes_by_name_maps_pass_state():
    results = [_result("a", True), _result("b", False)]
    assert outcomes_by_name(results) == {"other::a": True, "other::b": False}


def test_experiment_pairs_instructed_run_against_stripped_control(monkeypatch):
    def fake_run_tests(
        config,
        category=None,
        max_workers_override=None,
        instruction_ref=None,
        dry_run=False,
    ):
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


def test_repeated_experiment_alternates_arm_order_and_compares_a_git_ref(monkeypatch):
    calls = []

    def fake_run_tests(
        config,
        category=None,
        max_workers_override=None,
        instruction_ref=None,
        dry_run=False,
    ):
        calls.append(instruction_ref or "candidate")
        passed = instruction_ref is None
        return [_result("recovery", passed)]

    monkeypatch.setattr(run_evals_ab, "run_tests", fake_run_tests)
    config = {
        "tests": {
            "skills/humanize/reader_recovery": [
                {"name": "recovery", "prompt": "p", "skill_path": "s"}
            ]
        }
    }

    comparison = run_instruction_loading_experiment(
        config, epochs=3, comparison_ref="b13f3ebb"
    )

    assert calls == [
        "candidate",
        "b13f3ebb",
        "b13f3ebb",
        "candidate",
        "candidate",
        "b13f3ebb",
    ]
    assert comparison["method"] == "paired_hierarchical_bootstrap"
    assert comparison["epochs"] == 3
    assert comparison["variant_a_pass_rate"] == 1.0
    assert comparison["variant_b_pass_rate"] == 0.0


def test_experiment_refuses_to_grade_an_invocation_error(monkeypatch):
    def fake_run_tests(
        config,
        category=None,
        max_workers_override=None,
        instruction_ref=None,
        dry_run=False,
    ):
        result = _result("recovery", True)
        if instruction_ref:
            result.passed = False
            result.error = "session limit reached"
        return [result]

    monkeypatch.setattr(run_evals_ab, "run_tests", fake_run_tests)

    try:
        run_instruction_loading_experiment(
            {"tests": {"recovery": [{"name": "recovery", "prompt": "p"}]}},
            comparison_ref="base",
        )
    except RuntimeError as error:
        assert "control arm has invocation errors" in str(error)
    else:
        raise AssertionError("provider errors must not become model outcomes")


def test_dry_run_reaches_both_experiment_arms(monkeypatch):
    dry_run_values = []

    def fake_run_tests(
        config,
        category=None,
        max_workers_override=None,
        instruction_ref=None,
        dry_run=False,
    ):
        dry_run_values.append(dry_run)
        return [_result("recovery", True)]

    monkeypatch.setattr(run_evals_ab, "run_tests", fake_run_tests)

    comparison = run_instruction_loading_experiment(
        {"tests": {"recovery": [{"name": "recovery", "prompt": "p"}]}},
        dry_run=True,
    )

    assert comparison["n_paired"] == 1
    assert dry_run_values == [True, True]
