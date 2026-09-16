import benchmark_core

DESKTOP_ROWS = [
    "2026-01-01,wezterm,300.0,250.0,350.0,5",
    "2026-01-02,wezterm,320.0,280.0,360.0,5",
    "2026-01-01,tmux,20.0,15.0,25.0,5",
]

REBUILD_ROWS = [
    "2026-03-10T10:00:00+00:00,eval,kira/darwin,1.0,abc",
    "2026-03-10T10:01:00+00:00,eval,kira/darwin,3.0,abc",
    "2026-03-10T10:02:00+00:00,eval,rin/darwin,5.0,abc",
]

MALFORMED_ROWS = ["bad,line", "2026-01-01,tmux,not-a-number,1,1,1"]


class TestLatestValueByKey:
    def test_keeps_the_last_value_recorded_for_each_key(self):
        latest = benchmark_core.latest_value_by_key(DESKTOP_ROWS, (1,), 2)
        assert latest == {"wezterm": 320.0, "tmux": 20.0}

    def test_joins_several_key_columns(self):
        latest = benchmark_core.latest_value_by_key(REBUILD_ROWS, (1, 2), 3)
        assert latest == {"eval,kira/darwin": 3.0, "eval,rin/darwin": 5.0}

    def test_skips_short_and_unparseable_rows(self):
        assert benchmark_core.latest_value_by_key(MALFORMED_ROWS, (1,), 2) == {}

    def test_reads_nothing_from_no_rows(self):
        assert benchmark_core.latest_value_by_key([], (1,), 2) == {}


class TestAggregateValuesByKey:
    def test_sums_and_counts_every_value_for_a_key(self):
        aggregates = benchmark_core.aggregate_values_by_key(REBUILD_ROWS, (1, 2), 3)
        assert aggregates["eval,kira/darwin"].total == 4.0
        assert aggregates["eval,kira/darwin"].count == 2
        assert aggregates["eval,rin/darwin"].count == 1

    def test_aggregates_a_single_key_column(self):
        aggregates = benchmark_core.aggregate_values_by_key(DESKTOP_ROWS, (1,), 2)
        assert aggregates["wezterm"].total == 620.0
        assert aggregates["tmux"].count == 1

    def test_skips_short_and_unparseable_rows(self):
        assert benchmark_core.aggregate_values_by_key(MALFORMED_ROWS, (1,), 2) == {}


class TestRecentResultTableLines:
    def test_aligns_every_column_to_its_widest_field(self):
        lines = benchmark_core.recent_result_table_lines(
            ["timestamp,type", "2026-01-01,eval"], 20
        )
        assert lines == ["timestamp   type", "2026-01-01  eval"]

    def test_keeps_only_the_most_recent_rows_past_the_limit(self):
        rows = [f"2026-01-0{index},eval" for index in range(1, 5)]
        lines = benchmark_core.recent_result_table_lines(["timestamp,type", *rows], 2)
        assert len(lines) == 3
        assert lines[1].startswith("2026-01-03")
        assert lines[2].startswith("2026-01-04")

    def test_keeps_every_row_inside_the_limit(self):
        rows = ["2026-01-01,eval", "2026-01-02,eval"]
        lines = benchmark_core.recent_result_table_lines(["timestamp,type", *rows], 20)
        assert len(lines) == 3
