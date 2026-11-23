import benchmark_result_rows

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
    def test_joins_several_key_columns(self):
        latest = benchmark_result_rows.latest_value_by_key(REBUILD_ROWS, (1, 2), 3)
        assert latest == {"eval,kira/darwin": 3.0, "eval,rin/darwin": 5.0}

    def test_skips_short_and_unparseable_rows(self):
        assert benchmark_result_rows.latest_value_by_key(MALFORMED_ROWS, (1,), 2) == {}


class TestAggregateValuesByKey:
    def test_sums_and_counts_every_value_for_a_key(self):
        aggregates = benchmark_result_rows.aggregate_values_by_key(
            REBUILD_ROWS, (1, 2), 3
        )
        assert aggregates["eval,kira/darwin"].total == 4.0
        assert aggregates["eval,kira/darwin"].count == 2
        assert aggregates["eval,rin/darwin"].count == 1

    def test_skips_short_and_unparseable_rows(self):
        assert (
            benchmark_result_rows.aggregate_values_by_key(MALFORMED_ROWS, (1,), 2) == {}
        )


class TestRecentResultTableLines:
    def test_aligns_every_column_to_its_widest_field(self):
        lines = benchmark_result_rows.recent_result_table_lines(
            ["timestamp,type", "2026-01-01,eval"], 20
        )
        assert lines == ["timestamp   type", "2026-01-01  eval"]
