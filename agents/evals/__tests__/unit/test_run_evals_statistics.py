import pytest

from run_evals_statistics import (
    format_pass_rate_with_confidence_interval,
    wilson_score_interval,
)


def test_wilson_interval_brackets_the_point_estimate():
    lower, upper = wilson_score_interval(50, 100)
    assert lower < 0.5 < upper
    assert lower == pytest.approx(0.4038, abs=1e-3)
    assert upper == pytest.approx(0.5962, abs=1e-3)


def test_wilson_interval_stays_within_zero_to_one_at_the_boundaries():
    lower, upper = wilson_score_interval(100, 100)
    assert lower < 1.0
    assert upper <= 1.0
    lower, upper = wilson_score_interval(0, 100)
    assert lower == 0.0
    assert 0.0 < upper < 0.05


def test_wilson_interval_is_full_width_with_no_data():
    assert wilson_score_interval(0, 0) == (0.0, 1.0)


def test_wilson_interval_tightens_with_more_samples():
    small_sample = wilson_score_interval(5, 10)
    large_sample = wilson_score_interval(50, 100)
    assert (large_sample[1] - large_sample[0]) < (small_sample[1] - small_sample[0])


def test_pass_rate_line_reports_percentage_and_confidence_interval():
    line = format_pass_rate_with_confidence_interval(50, 100)
    assert "50.0%" in line
    assert "Wilson CI" in line
    assert "40.4%" in line
    assert "59.6%" in line


def test_pass_rate_line_handles_no_results():
    assert (
        format_pass_rate_with_confidence_interval(0, 0) == "Pass rate: n/a (no results)"
    )
