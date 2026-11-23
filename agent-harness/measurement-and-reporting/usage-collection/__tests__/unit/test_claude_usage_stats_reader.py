import json

from hypothesis import given
from hypothesis import strategies as st

import claude_usage_stats_reader

SAMPLE_STATS_CACHE = {
    "firstSessionDate": "2026-05-26T16:44:20.085Z",
    "lastComputedDate": "2026-06-17",
    "dailyActivity": [
        {
            "date": "2026-06-17",
            "messageCount": 42,
            "sessionCount": 5,
            "toolCallCount": 130,
        }
    ],
}


class TestReadStatsCache:
    def test_missing_file_returns_empty(self, tmp_path):
        assert (
            claude_usage_stats_reader.read_stats_cache(tmp_path / "absent.json") == {}
        )

    def test_corrupt_file_returns_empty(self, tmp_path):
        corrupt_path = tmp_path / "stats-cache.json"
        corrupt_path.write_text("{not json")
        assert claude_usage_stats_reader.read_stats_cache(corrupt_path) == {}

    def test_valid_file_is_parsed(self, tmp_path):
        valid_path = tmp_path / "stats-cache.json"
        valid_path.write_text(json.dumps(SAMPLE_STATS_CACHE))
        assert (
            claude_usage_stats_reader.read_stats_cache(valid_path)["lastComputedDate"]
            == "2026-06-17"
        )


def is_fully_measured_entry(entry) -> bool:
    return (
        entry["date"] != "bad"
        and isinstance(entry["messageCount"], int)
        and not isinstance(entry["messageCount"], bool)
        and entry["messageCount"] >= 0
    )


class TestSummarizeStatsCache:
    def test_empty_stats_cache_summarizes_to_unknown_activity(self):
        assert claude_usage_stats_reader.summarize_stats_cache({}) == {
            "stats_first_session_date": None,
            "activity_last_computed_date": None,
        }

    def test_summary_carries_no_model_usage_fields(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(
            {**SAMPLE_STATS_CACHE, "modelUsage": {"claude-opus-4-8": {}}}
        )
        assert set(summary) == {
            "stats_first_session_date",
            "activity_last_computed_date",
            "daily_activity",
        }

    def test_first_session_date_is_truncated_to_calendar_date(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["stats_first_session_date"] == "2026-05-26"

    def test_activity_keeps_the_original_cache_computed_date(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["activity_last_computed_date"] == "2026-06-17"

    @given(
        st.lists(
            st.fixed_dictionaries(
                {
                    "date": st.sampled_from(["2026-06-16", "2026-06-17", "bad"]),
                    "messageCount": st.one_of(
                        st.integers(min_value=-3, max_value=3), st.none(), st.booleans()
                    ),
                    "sessionCount": st.integers(min_value=0, max_value=3),
                    "toolCallCount": st.integers(min_value=0, max_value=3),
                }
            ),
            max_size=8,
        )
    )
    def test_daily_activity_is_reported_only_when_every_entry_is_fully_measured(
        self, entries
    ):
        summary = claude_usage_stats_reader.summarize_stats_cache(
            {"dailyActivity": entries}
        )
        if not all(is_fully_measured_entry(entry) for entry in entries):
            assert "daily_activity" not in summary
            return
        assert summary["daily_activity"] == [
            {
                "date": entry["date"],
                "message_count": entry["messageCount"],
                "session_count": entry["sessionCount"],
                "tool_call_count": entry["toolCallCount"],
            }
            for entry in entries
        ]
