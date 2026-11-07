from runner.execution import run_evals_subject_port as subject_port
from runner.execution import run_evals_test_runner
from runner import run_evals_worktree_and_environment as evaluation_environment
from runner.execution.run_evals_subject_port import (
    SubjectRequest,
    build_subject_invocation,
    model_for_harness,
)


def test_legacy_model_is_claude_only_and_harnesses_use_named_defaults():
    legacy = {"model": "haiku"}
    defaults = {"claude": "sonnet", "codex": "gpt-5.6-luna"}
    assert model_for_harness(legacy, "claude", defaults) == "haiku"
    assert model_for_harness(legacy, "codex", defaults) == "gpt-5.6-luna"
    assert model_for_harness(legacy, "opencode", defaults) is None


def test_alternate_harness_receives_its_named_model_only():
    named = {"models": {"codex": "gpt-5", "opencode": "anthropic/claude"}}
    defaults = {"claude": "sonnet", "codex": "gpt-5.6-luna"}
    assert model_for_harness(named, "codex", defaults) == "gpt-5"
    assert model_for_harness(named, "opencode", defaults) == "anthropic/claude"
    assert model_for_harness(named, "claude", defaults) == "sonnet"


def test_invocation_is_a_normalized_payload_without_provider_concepts(tmp_path):
    result_file = str(tmp_path / "result.json")
    invocation = build_subject_invocation(
        "codex",
        SubjectRequest(
            prompt="do it",
            model="gpt-5",
            model_reasoning_effort="low",
            system_prompt="SYS",
            timeout=90,
            max_turns=2,
        ),
        result_file,
    )
    assert invocation == {
        "harness": "codex",
        "prompt": "do it",
        "model": "gpt-5",
        "model_reasoning_effort": "low",
        "system_prompt": "SYS",
        "working_directory": str(evaluation_environment.EVAL_WORKING_DIRECTORY),
        "timeout": 90,
        "max_turns": 2,
        "no_tools": False,
        "result_file": result_file,
        "isolated_context": False,
    }


def test_subject_runner_passes_the_declared_turn_limit(monkeypatch):
    invocation = {}

    def invoke(harness, request, invocation_role):
        invocation.update(vars(request))
        return "candidate answer", True

    monkeypatch.setattr(subject_port, "invoke_subject", invoke)

    result = run_evals_test_runner.run_test(
        {
            "name": "bounded_subject",
            "prompt": "answer",
            "max_turns": 2,
            "assertions": {"output_contains": ["candidate"]},
        },
        settings={},
        harness="claude",
    )

    assert result.passed is True
    assert invocation["max_turns"] == 2
