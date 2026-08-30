import run_evals_subject_port as subject_port
from run_evals_subject_port import build_subject_invocation, model_for_harness


def test_legacy_model_is_claude_only_and_alternates_omit_unless_named():
    legacy = {"model": "haiku"}
    assert model_for_harness(legacy, "claude", "sonnet") == "haiku"
    assert model_for_harness(legacy, "claude", None) == "haiku"
    assert model_for_harness(legacy, "codex", "sonnet") is None
    assert model_for_harness(legacy, "opencode", "sonnet") is None


def test_alternate_harness_receives_its_named_model_only():
    named = {"models": {"codex": "gpt-5", "opencode": "anthropic/claude"}}
    assert model_for_harness(named, "codex", "sonnet") == "gpt-5"
    assert model_for_harness(named, "opencode", "sonnet") == "anthropic/claude"
    assert model_for_harness(named, "claude", "sonnet") == "sonnet"


def test_invocation_is_a_normalized_payload_without_provider_concepts():
    invocation = build_subject_invocation(
        "codex",
        prompt="do it",
        model="gpt-5",
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
        "system_prompt": "SYS",
        "working_directory": str(subject_port.EVAL_WORKING_DIRECTORY),
        "timeout": 90,
        "no_tools": False,
        "result_file": "/tmp/result.json",
    }
