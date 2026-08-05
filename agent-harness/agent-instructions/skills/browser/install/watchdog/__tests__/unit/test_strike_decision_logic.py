def test_strike_count_increments_when_cpu_at_or_above_threshold(watchdog_module):
    updated = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts={"100:5": 2},
        cpu_percent_by_process_key={"100:5": 150.0},
        runaway_threshold=130.0,
    )
    assert updated == {"100:5": 3}


def test_strike_count_resets_when_cpu_below_threshold(watchdog_module):
    updated = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts={"100:5": 3},
        cpu_percent_by_process_key={"100:5": 12.0},
        runaway_threshold=130.0,
    )
    assert updated == {"100:5": 0}


def test_strike_count_starts_at_one_for_unknown_process(watchdog_module):
    updated = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts={},
        cpu_percent_by_process_key={"200:9": 200.0},
        runaway_threshold=130.0,
    )
    assert updated == {"200:9": 1}


def test_strike_count_increments_exactly_at_threshold_boundary(watchdog_module):
    updated = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts={"300:1": 0},
        cpu_percent_by_process_key={"300:1": 130.0},
        runaway_threshold=130.0,
    )
    assert updated == {"300:1": 1}


def test_process_dropping_below_threshold_loses_accumulated_strikes(watchdog_module):
    first = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts={},
        cpu_percent_by_process_key={"400:2": 180.0},
        runaway_threshold=130.0,
    )
    second = watchdog_module.compute_updated_strike_counts(
        previous_strike_counts=first,
        cpu_percent_by_process_key={"400:2": 5.0},
        runaway_threshold=130.0,
    )
    assert second == {"400:2": 0}


def test_terminates_process_at_or_above_strike_limit(watchdog_module):
    to_terminate = watchdog_module.select_process_keys_to_terminate(
        strike_counts={"100:5": 4, "200:6": 2},
        consecutive_strikes_before_termination=4,
    )
    assert to_terminate == ["100:5"]


def test_does_not_terminate_process_one_strike_below_limit(watchdog_module):
    to_terminate = watchdog_module.select_process_keys_to_terminate(
        strike_counts={"100:5": 3},
        consecutive_strikes_before_termination=4,
    )
    assert to_terminate == []


def test_terminates_every_process_over_the_limit(watchdog_module):
    to_terminate = watchdog_module.select_process_keys_to_terminate(
        strike_counts={"100:5": 5, "200:6": 9, "300:7": 0},
        consecutive_strikes_before_termination=4,
    )
    assert sorted(to_terminate) == ["100:5", "200:6"]
