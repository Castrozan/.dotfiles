def test_round_trips_strike_counts_through_disk(watchdog_module, tmp_path):
    state_file_path = tmp_path / "strikes.json"
    strike_counts = {"100:5": 2, "200:6": 0}
    watchdog_module.write_persisted_strike_counts(state_file_path, strike_counts)
    assert (
        watchdog_module.read_persisted_strike_counts(state_file_path) == strike_counts
    )


def test_missing_state_file_reads_as_empty(watchdog_module, tmp_path):
    state_file_path = tmp_path / "does-not-exist.json"
    assert watchdog_module.read_persisted_strike_counts(state_file_path) == {}


def test_corrupt_state_file_reads_as_empty(watchdog_module, tmp_path):
    state_file_path = tmp_path / "corrupt.json"
    state_file_path.write_text("{not valid json")
    assert watchdog_module.read_persisted_strike_counts(state_file_path) == {}


def test_overwrites_prior_state_on_each_write(watchdog_module, tmp_path):
    state_file_path = tmp_path / "strikes.json"
    watchdog_module.write_persisted_strike_counts(state_file_path, {"100:5": 3})
    watchdog_module.write_persisted_strike_counts(state_file_path, {"200:6": 1})
    assert watchdog_module.read_persisted_strike_counts(state_file_path) == {"200:6": 1}
