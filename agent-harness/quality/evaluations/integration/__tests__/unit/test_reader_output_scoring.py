from integration_assertions_output import run_assertions
from integration_models import AssertionResult, SessionTrace
from integration_scoring import (
    calculate_experience_score,
    check_minimum_experience_score,
)


def test_output_assertions_grade_only_the_final_answer():
    trace = SessionTrace(
        assistant_messages=[
            "Earlier I mentioned base64 keys.",
            "Yes. contentCache is an in-memory map with no size limit.",
        ]
    )
    results = run_assertions(
        trace,
        {
            "output_contains": ["contentCache", "in-memory", "no size limit"],
            "output_not_contains": ["base64 keys"],
            "output_maximum_words": 12,
        },
    )
    assert all(result.passed for result in results)


def test_experience_score_rewards_reader_outcomes_not_punctuation():
    trace = SessionTrace(assistant_messages=["The cache exists — it is bounded."])
    assertions = [
        AssertionResult(name=str(index), passed=True, detail="passed")
        for index in range(4)
    ]
    assert calculate_experience_score(trace, assertions) == 77


def test_reader_scenario_can_require_a_minimum_experience_score():
    assert check_minimum_experience_score(89, 85).passed
    assert not check_minimum_experience_score(84, 85).passed
