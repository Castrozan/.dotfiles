import json

import render_usage_dashboard_data

SNAPSHOT_ONE = {
    "account_label": "acct1",
    "machine_label": "machA",
    "stats_first_session_date": "2026-06-01",
    "stats_last_computed_date": "2026-06-16",
    "daily_model_tokens": [
        {"date": "2026-06-16", "tokens_by_model": {"claude-opus-4-8": 100}},
    ],
    "model_usage_totals": {
        "claude-opus-4-8": {
            "input_tokens": 10,
            "output_tokens": 20,
            "cache_read_input_tokens": 1000,
            "cache_creation_input_tokens": 30,
            "cost_usd": 5,
        }
    },
    "memory_recall_savings": {
        "suppressed_recall_event_total": 4,
        "dedup_suppressed_character_total": 200,
        "suppressed_recall_event_count_by_reason": {"dedup": 3, "budget": 1},
    },
}

SNAPSHOT_TWO = {
    "account_label": "acct1",
    "machine_label": "machB",
    "stats_first_session_date": "2026-05-20",
    "stats_last_computed_date": "2026-06-17",
    "daily_model_tokens": [
        {"date": "2026-06-16", "tokens_by_model": {"claude-opus-4-8": 50}},
        {"date": "2026-06-17", "tokens_by_model": {"claude-haiku-4-5": 7}},
    ],
    "model_usage_totals": {
        "claude-opus-4-8": {
            "cache_read_input_tokens": 500,
            "output_tokens": 5,
        }
    },
    "memory_recall_savings": {
        "suppressed_recall_event_total": 1,
        "dedup_suppressed_character_total": 80,
        "suppressed_recall_event_count_by_reason": {"debounce": 1},
    },
}

SNAPSHOT_OTHER_ACCOUNT = {
    "account_label": "acct2",
    "machine_label": "machA",
    "stats_first_session_date": "2026-06-10",
    "stats_last_computed_date": "2026-06-17",
    "daily_model_tokens": [
        {"date": "2026-06-17", "tokens_by_model": {"claude-opus-4-8": 9}},
    ],
    "model_usage_totals": {"claude-opus-4-8": {"cache_read_input_tokens": 99}},
    "memory_recall_savings": {},
}


def _write_snapshot(snapshot_directory, name, snapshot):
    (snapshot_directory / f"{name}.json").write_text(json.dumps(snapshot))


class TestReadUsageSnapshots:
    def test_missing_directory_returns_empty(self, tmp_path):
        assert render_usage_dashboard_data.read_usage_snapshots(tmp_path / "x") == []

    def test_corrupt_snapshot_is_skipped(self, tmp_path):
        _write_snapshot(tmp_path, "good", SNAPSHOT_ONE)
        (tmp_path / "bad.json").write_text("{not json")
        snapshots = render_usage_dashboard_data.read_usage_snapshots(tmp_path)
        assert len(snapshots) == 1


class TestGroupSnapshotsByAccount:
    def test_machines_of_same_account_are_merged(self):
        accounts = render_usage_dashboard_data.group_snapshots_by_account(
            [SNAPSHOT_ONE, SNAPSHOT_TWO]
        )
        assert len(accounts) == 1
        account = accounts[0]
        assert account["account_label"] == "acct1"
        assert account["machine_count"] == 2
        assert account["token_totals"]["cache_read_input_tokens"] == 1500
        assert account["token_totals"]["output_tokens"] == 25
        assert account["daily_total_tokens"]["2026-06-16"] == 150
        assert account["first_session_date"] == "2026-05-20"
        assert account["last_computed_date"] == "2026-06-17"

    def test_savings_reasons_are_summed_across_machines(self):
        accounts = render_usage_dashboard_data.group_snapshots_by_account(
            [SNAPSHOT_ONE, SNAPSHOT_TWO]
        )
        savings = accounts[0]["memory_recall_savings"]
        assert savings["suppressed_recall_event_total"] == 5
        assert savings["dedup_suppressed_character_total"] == 280
        assert savings["suppressed_recall_event_count_by_reason"] == {
            "dedup": 3,
            "budget": 1,
            "debounce": 1,
        }

    def test_distinct_accounts_stay_separate_and_sorted(self):
        accounts = render_usage_dashboard_data.group_snapshots_by_account(
            [SNAPSHOT_OTHER_ACCOUNT, SNAPSHOT_ONE]
        )
        assert [account["account_label"] for account in accounts] == ["acct1", "acct2"]


class TestBuildUsageViewModel:
    def test_view_model_summary_and_chart(self, tmp_path):
        _write_snapshot(tmp_path, "one", SNAPSHOT_ONE)
        _write_snapshot(tmp_path, "two", SNAPSHOT_TWO)
        _write_snapshot(tmp_path, "other", SNAPSHOT_OTHER_ACCOUNT)
        view_model = render_usage_dashboard_data.build_usage_view_model(tmp_path)
        assert view_model["summary"]["account_count"] == 2
        assert view_model["summary"]["machine_count"] == 3
        assert view_model["summary"]["token_totals"]["cache_read_input_tokens"] == 1599
        assert view_model["chart"]["dates"] == ["2026-06-16", "2026-06-17"]
        first_account_series = view_model["chart"]["series"][0]
        assert first_account_series["account_label"] == "acct1"
        assert first_account_series["values"] == [150, 7]
