import json

import pytest
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

    def test_non_object_file_returns_empty(self, tmp_path):
        list_path = tmp_path / "stats-cache.json"
        list_path.write_text("[1, 2]")
        assert claude_usage_stats_reader.read_stats_cache(list_path) == {}

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

    def test_explicitly_measured_empty_activity_stays_a_measured_zero(self):
        assert (
            claude_usage_stats_reader.summarize_stats_cache({"dailyActivity": []})[
                "daily_activity"
            ]
            == []
        )

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

    def test_daily_activity_keys_are_snake_cased(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["daily_activity"][0] == {
            "date": "2026-06-17",
            "message_count": 42,
            "session_count": 5,
            "tool_call_count": 130,
        }

    @pytest.mark.parametrize(
        "unmeasured_entry",
        [
            pytest.param(
                {"date": "2026-06-17", "sessionCount": 5, "toolCallCount": 1},
                id="missing-counter",
            ),
            pytest.param(
                {
                    "date": "2026-06-17",
                    "messageCount": -1,
                    "sessionCount": 0,
                    "toolCallCount": 0,
                },
                id="negative-counter",
            ),
            pytest.param(
                {
                    "date": "2026-06-17",
                    "messageCount": True,
                    "sessionCount": 0,
                    "toolCallCount": 0,
                },
                id="boolean-counter",
            ),
            pytest.param(
                {
                    "date": "2026-06-17",
                    "messageCount": 1.5,
                    "sessionCount": 0,
                    "toolCallCount": 0,
                },
                id="fractional-counter",
            ),
            pytest.param(
                {
                    "date": "2026-6-17",
                    "messageCount": 1,
                    "sessionCount": 0,
                    "toolCallCount": 0,
                },
                id="non-canonical-date",
            ),
            pytest.param("not-an-object", id="non-object-entry"),
        ],
    )
    def test_partially_unmeasured_activity_omits_the_whole_list(self, unmeasured_entry):
        summary = claude_usage_stats_reader.summarize_stats_cache(
            {
                "dailyActivity": [
                    unmeasured_entry,
                    SAMPLE_STATS_CACHE["dailyActivity"][0],
                ]
            }
        )
        assert "daily_activity" not in summary

    @pytest.mark.parametrize(
        "daily_activity",
        [None, {}, "not-a-list", 0],
        ids=["null", "object", "string", "number"],
    )
    def test_non_list_daily_activity_is_omitted_as_unknown(self, daily_activity):
        summary = claude_usage_stats_reader.summarize_stats_cache(
            {"dailyActivity": daily_activity}
        )
        assert "daily_activity" not in summary

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
