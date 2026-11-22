from hypothesis import given
from hypothesis import strategies as st

from fix_loop_options import (
    DONE,
    ESCALATE,
    MERGE,
    RETRY,
    RETRY_DEEPER,
    LoopState,
    merge_options,
    next_step_options,
)

signatures = st.sampled_from(["", "aebd96662dadc127", "0f3c1a"])
loop_states = st.builds(
    LoopState,
    passed=st.booleans(),
    iteration=st.integers(1, 8),
    max_iterations=st.integers(1, 6),
    failure_signature=signatures,
    previous_signature=signatures,
)
findings = st.lists(
    st.fixed_dictionaries(
        {"severity": st.sampled_from(["critical", "high", "medium", "low", "odd"])}
    ),
    max_size=4,
)
loop_choices = st.sampled_from([DONE, RETRY, RETRY_DEEPER, ESCALATE, ""])


def model_may_choose_only_with_an_escape(options: tuple[str, ...]) -> bool:
    return len(options) == 1 or ESCALATE in options


@given(state=loop_states)
def test_next_step_options_stay_in_the_table_and_keep_escalate_open(state):
    legal = next_step_options(state)
    assert set(legal.options) <= {DONE, RETRY, RETRY_DEEPER, ESCALATE}
    assert model_may_choose_only_with_an_escape(legal.options)


@given(state=loop_states)
def test_hard_stops_override_the_model(state):
    legal = next_step_options(state)
    if state.passed:
        assert legal.options == (DONE,)
    elif state.iteration >= state.max_iterations:
        assert (legal.options, legal.guarded) == ((ESCALATE,), True)
    elif state.failure_signature == state.previous_signature:
        assert (legal.options, legal.guarded) == ((ESCALATE,), True)
    else:
        assert legal.options == (RETRY, RETRY_DEEPER, ESCALATE)


@given(loop_choice=loop_choices, review=findings)
def test_merge_is_legal_only_after_green_tests_without_blocking_findings(
    loop_choice, review
):
    legal = merge_options(loop_choice, review)
    blocked = any(finding["severity"] in {"critical", "high"} for finding in review)
    assert set(legal.options) <= {MERGE, ESCALATE}
    assert model_may_choose_only_with_an_escape(legal.options)
    assert (MERGE in legal.options) == (loop_choice == DONE and not blocked)


@given(review=findings)
def test_a_clean_review_after_green_tests_settles_without_a_model(review):
    legal = merge_options(DONE, review)
    assert (legal.options == (MERGE,)) == (not review)
