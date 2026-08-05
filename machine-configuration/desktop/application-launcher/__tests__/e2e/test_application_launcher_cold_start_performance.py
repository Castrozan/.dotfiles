import statistics
import time

from application_launcher_test_helpers import (
    measure_one_socket_to_picker_visible_in_milliseconds,
)

WARMUP_RUN_COUNT_BEFORE_MEASUREMENT = 1
MEASUREMENT_SAMPLE_COUNT = 5
INTER_RUN_SLEEP_SECONDS = 0.15
WARM_PICKER_VISIBLE_MEDIAN_THRESHOLD_MILLISECONDS = 50
WARM_PICKER_VISIBLE_HARD_OUTLIER_CEILING_MILLISECONDS = 200


def collect_warm_socket_to_picker_visible_samples():
    for _ in range(WARMUP_RUN_COUNT_BEFORE_MEASUREMENT):
        measure_one_socket_to_picker_visible_in_milliseconds()
        time.sleep(INTER_RUN_SLEEP_SECONDS)
    elapsed_samples_milliseconds = []
    last_run_milestones = []
    for run_index in range(MEASUREMENT_SAMPLE_COUNT):
        picker_visible_elapsed_milliseconds, captured_milestones = (
            measure_one_socket_to_picker_visible_in_milliseconds()
        )
        assert picker_visible_elapsed_milliseconds is not None, (
            f"run {run_index}: picker-visible milestone missing."
            f" captured milestones: {captured_milestones}"
        )
        elapsed_samples_milliseconds.append(picker_visible_elapsed_milliseconds)
        last_run_milestones = captured_milestones
        time.sleep(INTER_RUN_SLEEP_SECONDS)
    return elapsed_samples_milliseconds, last_run_milestones


def print_warm_cold_start_summary(elapsed_samples_milliseconds, last_run_milestones):
    print("warm socket-to-picker-visible (daemon):")
    print(f"  samples (ms): {[f'{e:.1f}' for e in elapsed_samples_milliseconds]}")
    print(
        f"  min={min(elapsed_samples_milliseconds):.1f}ms"
        f"  median={statistics.median(elapsed_samples_milliseconds):.1f}ms"
        f"  avg={statistics.mean(elapsed_samples_milliseconds):.1f}ms"
        f"  max={max(elapsed_samples_milliseconds):.1f}ms"
    )
    print("  last run milestones:")
    for elapsed_milliseconds, label in last_run_milestones:
        print(f"    {elapsed_milliseconds:7.1f}ms  {label}")


def test_warm_socket_to_picker_visible_median_is_below_target_threshold():
    elapsed_samples_milliseconds, last_run_milestones = (
        collect_warm_socket_to_picker_visible_samples()
    )
    print_warm_cold_start_summary(elapsed_samples_milliseconds, last_run_milestones)
    median_elapsed_milliseconds = statistics.median(elapsed_samples_milliseconds)
    assert (
        median_elapsed_milliseconds < WARM_PICKER_VISIBLE_MEDIAN_THRESHOLD_MILLISECONDS
    ), (
        f"warm median {median_elapsed_milliseconds:.1f}ms exceeds target"
        f" {WARM_PICKER_VISIBLE_MEDIAN_THRESHOLD_MILLISECONDS}ms"
    )


def test_warm_socket_to_picker_visible_max_stays_under_outlier_ceiling():
    elapsed_samples_milliseconds, _ = collect_warm_socket_to_picker_visible_samples()
    maximum_elapsed_milliseconds = max(elapsed_samples_milliseconds)
    assert (
        maximum_elapsed_milliseconds
        < WARM_PICKER_VISIBLE_HARD_OUTLIER_CEILING_MILLISECONDS
    ), (
        f"warm max {maximum_elapsed_milliseconds:.1f}ms exceeds outlier ceiling"
        f" {WARM_PICKER_VISIBLE_HARD_OUTLIER_CEILING_MILLISECONDS}ms."
        f" samples: {elapsed_samples_milliseconds}"
    )
