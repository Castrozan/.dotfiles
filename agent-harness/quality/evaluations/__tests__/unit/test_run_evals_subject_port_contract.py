import run_evals_subject_port as subject_port
from run_evals_subject_port import build_subject_invocation, model_for_harness


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


def test_invocation_is_a_normalized_payload_without_provider_concepts():
    invocation = build_subject_invocation(
        "codex",
        prompt="do it",
        model="gpt-5",
        model_reasoning_effort="low",
        system_prompt="SYS",
        timeout=90,
        no_tools=False,
        working_directory=None,
        result_file="/tmp/result.json",
    )
    assert invocation == {
        "harness": "codex",
        "prompt": "do it",
        "model": "gpt-5",
        "model_reasoning_effort": "low",
        "system_prompt": "SYS",
        "working_directory": str(subject_port.EVAL_WORKING_DIRECTORY),
        "timeout": 90,
        "no_tools": False,
        "result_file": "/tmp/result.json",
    }
