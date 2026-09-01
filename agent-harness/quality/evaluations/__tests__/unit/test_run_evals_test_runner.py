import run_evals_subject_port as subject_port
import run_evals_suite_runner
import run_evals_test_runner
from run_evals_suite_runner import run_tests
from run_evals_test_runner import TestResult


def _echo_run_test(
    test,
    settings,
    dry_run,
    authored_category="other",
    instruction_ref=None,
    harness="claude",
    judge_harness="claude",
):
    return TestResult(
        name=test["name"],
        passed=True,
        duration=0.0,
        output=test["prompt"],
        assertions_failed=[],
        category=authored_category,
    )


def test_parallel_run_keeps_results_for_duplicate_test_names(monkeypatch):
    monkeypatch.setattr(run_evals_suite_runner, "run_test", _echo_run_test)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "category_one": [{"name": "dup", "prompt": "prompt-A"}],
            "category_two": [{"name": "dup", "prompt": "prompt-B"}],
        },
    }

    results = run_tests(config)

    assert len(results) == 2
    assert {result.output for result in results} == {"prompt-A", "prompt-B"}


def test_run_tests_tags_each_result_with_its_authored_category(monkeypatch):
    monkeypatch.setattr(run_evals_suite_runner, "run_test", _echo_run_test)
    config = {
        "settings": {"parallel_workers": 2},
        "tests": {
            "workflow_compliance": [
                {"name": "a", "prompt": "p"},
                {"name": "b", "prompt": "p"},
            ],
            "skill_routing": [{"name": "c", "prompt": "p"}],
        },
    }

    results = run_tests(config)

    category_by_name = {result.name: result.category for result in results}
    assert category_by_name == {
        "a": "workflow_compliance",
        "b": "workflow_compliance",
        "c": "skill_routing",
    }


def test_serial_single_test_still_carries_authored_category(monkeypatch):
    monkeypatch.setattr(run_evals_suite_runner, "run_test", _echo_run_test)
    config = {
        "settings": {},
        "tests": {"core_rules": [{"name": "only", "prompt": "p"}]},
    }

    results = run_tests(config)

    assert len(results) == 1
    assert results[0].category == "core_rules"


def test_model_invocation_failure_is_reported_without_judging_its_error_text(
    monkeypatch,
):
    monkeypatch.setattr(
        subject_port,
        "invoke_subject",
        lambda harness, **kwargs: ("session limit reached", False),
    )

    result = run_evals_test_runner.run_test(
        {
            "name": "provider_limit",
            "prompt": "answer",
            "assertions": {"llm_judge": ["must answer"]},
        },
        settings={},
    )

    assert result.passed is False
    assert result.error == "session limit reached"
    assert result.assertions_failed == []


def test_judge_invocation_failure_is_an_evaluation_error(monkeypatch):
    invocations = iter((("candidate answer", True), ("session limit reached", False)))
    monkeypatch.setattr(
        subject_port,
        "invoke_subject",
        lambda harness, **kwargs: next(invocations),
    )

    result = run_evals_test_runner.run_test(
        {
            "name": "judge_provider_limit",
            "prompt": "answer",
            "assertions": {"llm_judge": ["must answer"]},
        },
        settings={},
    )

    assert result.passed is False
    assert result.error.startswith("judge invocation failed")
    assert result.assertions_failed == []


def test_codex_subject_and_judge_use_their_pinned_models_and_reasoning(monkeypatch):
    invocations = []

    def invoke(harness, **kwargs):
        invocations.append((harness, kwargs))
        if kwargs["invocation_role"] == "judge":
            return "VERDICT: PASS", True
        return "candidate answer", True

    monkeypatch.setattr(subject_port, "invoke_subject", invoke)
    settings = {
        "subject_models": {"codex": "gpt-5.6-sol"},
        "subject_reasoning_efforts": {"codex": "medium"},
        "judge_models": {"codex": "gpt-5.6-luna"},
        "judge_reasoning_efforts": {"codex": "low"},
    }

    result = run_evals_test_runner.run_test(
        {
            "name": "codex_profile",
            "prompt": "answer",
            "assertions": {"llm_judge": ["must answer"]},
        },
        settings=settings,
        harness="codex",
        judge_harness="codex",
    )

    assert result.passed is True
    assert invocations[0][0] == "codex"
    assert invocations[0][1]["model"] == "gpt-5.6-sol"
    assert invocations[0][1]["model_reasoning_effort"] == "high"
    assert invocations[0][1]["invocation_role"] == "subject"
    assert invocations[1][0] == "codex"
    assert invocations[1][1]["model"] == "gpt-5.6-luna"
    assert invocations[1][1]["model_reasoning_effort"] == "low"
    assert invocations[1][1]["invocation_role"] == "judge"


def test_opencode_subject_and_judge_can_use_provider_default_models(monkeypatch):
    invocations = []

    def invoke(harness, **keyword_arguments):
        invocations.append((harness, keyword_arguments))
        if keyword_arguments["invocation_role"] == "judge":
            return "VERDICT: PASS", True
        return "candidate answer", True

    monkeypatch.setattr(subject_port, "invoke_subject", invoke)
    result = run_evals_test_runner.run_test(
        {
            "name": "opencode_defaults",
            "prompt": "answer",
            "assertions": {"llm_judge": ["must answer"]},
        },
        settings={"subject_models": {}, "judge_models": {}},
        harness="opencode",
        judge_harness="opencode",
    )

    assert result.passed is True
    assert [invocation[1]["model"] for invocation in invocations] == [None, None]
