import datetime
import importlib.util
import pathlib
import sys


def _load_restart_scheduling_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "agent-wrapper"
        / "restart_scheduling.py"
    )
    module_spec = importlib.util.spec_from_file_location(
        "restart_scheduling", module_path
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["restart_scheduling"] = module
    module_spec.loader.exec_module(module)
    return module


restart_scheduling = _load_restart_scheduling_module()


def test_seconds_until_active_hours_start_never_returns_zero_just_before_boundary():
    now_just_before_eight = datetime.datetime(2026, 5, 25, 7, 59, 59, 999_000)
    sleep_seconds = restart_scheduling.seconds_until_active_hours_start(
        8, now=now_just_before_eight
    )
    assert sleep_seconds >= 1, (
        "sleep_seconds must be >= 1 to avoid a busy loop when sub-second remains"
    )


def test_seconds_until_active_hours_start_does_not_skip_whole_day_just_after_boundary():
    now_just_after_eight = datetime.datetime(2026, 5, 25, 8, 0, 0, 1_000)
    sleep_seconds = restart_scheduling.seconds_until_active_hours_start(
        8, now=now_just_after_eight
    )
    assert sleep_seconds < 60, (
        f"crossing the boundary by 1ms must not schedule a 24h sleep; got {sleep_seconds}s"
    )


def test_is_within_active_hours_is_true_at_exact_start_hour():
    now_at_eight = datetime.datetime(2026, 5, 25, 8, 0, 0)
    assert restart_scheduling.is_within_active_hours(8, 20, now=now_at_eight) is True


def test_is_within_active_hours_is_false_just_before_start_hour():
    now_just_before_eight = datetime.datetime(2026, 5, 25, 7, 59, 59)
    assert (
        restart_scheduling.is_within_active_hours(8, 20, now=now_just_before_eight)
        is False
    )


def test_is_within_active_hours_handles_overnight_window():
    now_at_midnight = datetime.datetime(2026, 5, 25, 0, 0, 0)
    assert restart_scheduling.is_within_active_hours(22, 6, now=now_at_midnight) is True
    now_at_noon = datetime.datetime(2026, 5, 25, 12, 0, 0)
    assert restart_scheduling.is_within_active_hours(22, 6, now=now_at_noon) is False


def test_seconds_until_active_hours_start_targets_today_when_start_in_future():
    now_at_six_am = datetime.datetime(2026, 5, 25, 6, 0, 0)
    sleep_seconds = restart_scheduling.seconds_until_active_hours_start(
        8, now=now_at_six_am
    )
    assert sleep_seconds == 2 * 60 * 60


def test_seconds_until_active_hours_start_targets_tomorrow_when_start_passed():
    now_at_ten_pm = datetime.datetime(2026, 5, 25, 22, 0, 0)
    sleep_seconds = restart_scheduling.seconds_until_active_hours_start(
        8, now=now_at_ten_pm
    )
    assert sleep_seconds == 10 * 60 * 60


def test_should_reset_backoff_true_for_long_stable_run():
    assert restart_scheduling.should_reset_backoff(120, was_stuck_kill=False) is True


def test_should_reset_backoff_false_when_long_run_ended_in_stuck_kill():
    assert restart_scheduling.should_reset_backoff(120, was_stuck_kill=True) is False


def test_should_reset_backoff_false_for_short_run():
    assert restart_scheduling.should_reset_backoff(5, was_stuck_kill=False) is False
