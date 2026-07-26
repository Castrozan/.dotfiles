from run_evals_baseline import MAXIMUM_BASELINE_AGE_DAYS
from run_evals_baseline_history import baseline_staleness_failure


def test_a_baseline_inside_the_freshness_window_is_not_a_failure():
    assert baseline_staleness_failure(0, 30) is None
    assert baseline_staleness_failure(30, 30) is None


def test_a_baseline_past_the_freshness_window_fails_and_names_the_remedy():
    failure = baseline_staleness_failure(31, 30)
    assert failure is not None
    assert "31" in failure
    assert "save-baseline" in failure


def test_the_configured_freshness_window_is_a_usable_number_of_days():
    assert 7 <= MAXIMUM_BASELINE_AGE_DAYS <= 90
