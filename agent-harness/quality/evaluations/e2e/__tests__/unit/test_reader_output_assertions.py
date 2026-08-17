from e2e_assertions import run_e2e_assertions
from e2e_models import E2eAssertionResult, TerminalSessionTrace
from e2e_scoring import (
    calculate_e2e_experience_score,
    check_minimum_e2e_experience_score,
)


def test_reader_assertions_grade_the_final_transcript_message():
    trace = TerminalSessionTrace(
        detected_assistant_text_blocks=[
            "Earlier I mentioned base64 keys.",
            "Yes. contentCache is an in-memory map with no size limit.",
        ]
    )
    results = run_e2e_assertions(
        trace,
        {
            "output_contains": ["contentCache", "in-memory", "no size limit"],
            "output_not_contains": ["base64 keys"],
            "output_maximum_words": 12,
        },
    )
    assert all(result.passed for result in results)


def test_e2e_score_rewards_reader_outcomes_not_punctuation():
    trace = TerminalSessionTrace(
        detected_assistant_text_blocks=["The cache exists — it is bounded."]
    )
    assertions = [
        E2eAssertionResult(name=str(index), passed=True, detail="passed")
        for index in range(4)
    ]
    assert calculate_e2e_experience_score(trace, assertions) == 77


def test_reader_scenario_can_require_a_minimum_experience_score():
    assert check_minimum_e2e_experience_score(89, 85).passed
    assert not check_minimum_e2e_experience_score(84, 85).passed
