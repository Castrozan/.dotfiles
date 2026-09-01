import run_evals_subject_port as subject_port
from run_evals_provider_usage import provider_usage_summary, reset_provider_usage
from run_evals_subject_port import invoke_subject


def test_usage_is_normalized_by_role_and_harness(monkeypatch):
    monkeypatch.setattr(
        subject_port.subprocess,
        "run",
        lambda command, **keyword_arguments: None,
    )
    monkeypatch.setattr(subject_port, "resolve_node_runtime", lambda: "/bin/runtime")
    monkeypatch.setattr(
        subject_port,
        "read_result_file",
        lambda path: {
            "output": "graded",
            "error": None,
            "usage": {
                "input_tokens": 120,
                "cached_input_tokens": 80,
                "output_tokens": 12,
                "reasoning_output_tokens": 4,
            },
        },
    )
    reset_provider_usage()

    output, invoked = invoke_subject("codex", prompt="q", invocation_role="judge")

    assert invoked is True
    assert output == "graded"
    assert provider_usage_summary() == {
        "judge": {
            "codex": {
                "invocations": 1,
                "measured_invocations": 1,
                "input_tokens": 120,
                "cached_input_tokens": 80,
                "cache_write_input_tokens": 0,
                "output_tokens": 12,
                "reasoning_output_tokens": 4,
            }
        }
    }
