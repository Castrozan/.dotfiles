from runner.execution import run_evals_subject_port as subject_port
from runner.execution import run_evals_test_runner


def test_judging_receives_the_original_request_and_preserves_its_explanation(
    monkeypatch,
):
    invocations = []
    outputs = iter(
        (
            ("Use a list.", True),
            (
                "The request requires a table; the response uses a list.\nVERDICT: FAIL",
                True,
            ),
        )
    )

    def invoke(harness, **arguments):
        invocations.append(arguments)
        return next(outputs)

    monkeypatch.setattr(subject_port, "invoke_subject", invoke)
    result = run_evals_test_runner.run_test(
        {
            "name": "contextual_judgment",
            "prompt": "Map the three harnesses to loading surfaces in a table.",
            "assertions": {"llm_judge": ["Uses the requested format."]},
        },
        settings={},
        harness="codex",
        judge_harness="codex",
    )

    assert result.passed is False
    assert result.error is None
    assert (
        "Map the three harnesses to loading surfaces in a table."
        in invocations[1]["prompt"]
    )
    assert (
        "The request requires a table; the response uses a list."
        in result.assertions_failed[0]
    )
