import json

import usage_snapshot_writer

SAMPLE_STATS_SUMMARY = {
    "stats_first_session_date": "2026-05-26",
    "stats_last_computed_date": "2026-06-17",
    "daily_model_tokens": [
        {"date": "2026-06-17", "tokens_by_model": {"claude-opus-4-8": 3400}}
    ],
    "daily_activity": [],
    "model_usage_totals": {"claude-opus-4-8": {"cache_read_input_tokens": 15970324893}},
}

SAMPLE_SAVINGS = {
    "memory_recall_session_count": 2,
    "dedup_suppressed_character_total": 200,
}


class TestBuildUsageSnapshot:
    def test_snapshot_carries_labels_and_schema_version(self):
        snapshot = usage_snapshot_writer.build_usage_snapshot(
            "acct123", "mach456", SAMPLE_STATS_SUMMARY, SAMPLE_SAVINGS
        )
        assert snapshot["account_label"] == "acct123"
        assert snapshot["machine_label"] == "mach456"
        assert (
            snapshot["schema_version"]
            == usage_snapshot_writer.USAGE_SNAPSHOT_SCHEMA_VERSION
        )

    def test_snapshot_folds_in_stats_summary_and_savings(self):
        snapshot = usage_snapshot_writer.build_usage_snapshot(
            "acct123", "mach456", SAMPLE_STATS_SUMMARY, SAMPLE_SAVINGS
        )
        assert snapshot["stats_last_computed_date"] == "2026-06-17"
        assert (
            snapshot["model_usage_totals"]["claude-opus-4-8"]["cache_read_input_tokens"]
            == 15970324893
        )
        assert snapshot["memory_recall_savings"] == SAMPLE_SAVINGS

    def test_snapshot_carries_no_raw_account_identifier(self):
        snapshot = usage_snapshot_writer.build_usage_snapshot(
            "acct123", "mach456", SAMPLE_STATS_SUMMARY, SAMPLE_SAVINGS
        )
        assert "oauthAccount" not in json.dumps(snapshot)
        assert "emailAddress" not in json.dumps(snapshot)


class TestWriteUsageSnapshot:
    def test_snapshot_file_name_combines_labels(self):
        assert (
            usage_snapshot_writer.usage_snapshot_file_name("acct123", "mach456")
            == "acct123-mach456.json"
        )

    def test_write_creates_directory_and_keyed_file(self, tmp_path):
        snapshot = usage_snapshot_writer.build_usage_snapshot(
            "acct123", "mach456", SAMPLE_STATS_SUMMARY, SAMPLE_SAVINGS
        )
        snapshot_directory = tmp_path / "snapshots"
        written_path = usage_snapshot_writer.write_usage_snapshot(
            snapshot_directory, snapshot
        )
        assert written_path == snapshot_directory / "acct123-mach456.json"
        assert json.loads(written_path.read_text())["account_label"] == "acct123"

    def test_written_snapshot_is_sorted_and_newline_terminated(self, tmp_path):
        snapshot = usage_snapshot_writer.build_usage_snapshot(
            "acct123", "mach456", SAMPLE_STATS_SUMMARY, SAMPLE_SAVINGS
        )
        written_path = usage_snapshot_writer.write_usage_snapshot(tmp_path, snapshot)
        written_text = written_path.read_text()
        assert written_text.endswith("\n")
        assert written_text.index('"account_label"') < written_text.index(
            '"schema_version"'
        )
