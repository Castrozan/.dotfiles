from datetime import datetime, timezone

from run_evals_baseline_history import (
    baseline_evidence_age_days,
    baseline_staleness_failure,
)
from run_evals_baseline_thresholds import MAXIMUM_BASELINE_AGE_DAYS


def test_materialized_baseline_age_uses_its_oldest_evidence():
    baseline = {
        "generated_at": "2026-09-01T00:00:00+00:00",
        "oldest_evidence_at": "2026-07-31T00:00:00+00:00",
    }

    assert (
        baseline_evidence_age_days(baseline, datetime(2026, 9, 1, tzinfo=timezone.utc))
        == 32
    )


def test_legacy_baseline_age_uses_its_generation_time():
    baseline = {"generated_at": "2026-08-31T00:00:00+00:00"}

    assert (
        baseline_evidence_age_days(baseline, datetime(2026, 9, 1, tzinfo=timezone.utc))
        == 1
    )


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
