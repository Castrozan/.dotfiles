from copy import deepcopy

import pytest

from runner import run_evals_configuration_contract


def configured_test():
    return {
        "name": "example",
        "prompt": "Answer the question",
        "assertions": {"output_contains": ["answer"]},
    }


@pytest.mark.parametrize(
    "invalid_assertions",
    (
        {},
        {"contains": ["answer"]},
        "output_contains",
        {"output_contains": []},
        {"output_contains": "answer"},
        {"llm_judge": [{"rubric": ""}]},
    ),
)
def test_unknown_or_empty_assertions_cannot_bypass_evaluation_coverage(
    invalid_assertions,
):
    test = configured_test()
    test["assertions"] = invalid_assertions

    failures = run_evals_configuration_contract.evaluation_configuration_failures(
        {"tests": {"suite": [test]}}
    )

    assert failures
    assert "assertion" in failures[0]


def test_duplicate_case_names_cannot_hide_a_current_test():
    test = configured_test()

    failures = run_evals_configuration_contract.evaluation_configuration_failures(
        {"tests": {"suite": [test, deepcopy(test)]}}
    )

    assert failures == ["suite: duplicate evaluation name example"]


def test_missing_extra_instruction_sources_fail_before_model_invocation(
    tmp_path, monkeypatch
):
    test = configured_test()
    test["extra_skill_paths"] = ["missing.md"]
    monkeypatch.setattr(run_evals_configuration_contract, "REPO_ROOT", tmp_path)

    failures = run_evals_configuration_contract.evaluation_configuration_failures(
        {"tests": {"suite": [test]}}
    )

    assert failures == ["suite::example: missing instruction source missing.md"]


def test_hook_cases_keep_their_native_assertion_contract_without_a_model_prompt():
    test = {
        "name": "hook_case",
        "type": "hook_test",
        "assertions": {"hook_blocks": False, "message_contains": "expected"},
    }

    assert (
        run_evals_configuration_contract.evaluation_configuration_failures(
            {"tests": {"suite": [test]}}
        )
        == []
    )


def test_exact_empty_output_remains_a_meaningful_assertion():
    test = configured_test()
    test["assertions"] = {"output_equals": [""]}

    assert (
        run_evals_configuration_contract.evaluation_configuration_failures(
            {"tests": {"suite": [test]}}
        )
        == []
    )


def test_explicit_system_prompts_use_the_same_source_precedence_as_the_runner():
    test = configured_test()
    test.update(system_prompt="Explicit instructions", skill_path="unused-missing.md")

    assert (
        run_evals_configuration_contract.evaluation_configuration_failures(
            {"tests": {"suite": [test]}}
        )
        == []
    )
