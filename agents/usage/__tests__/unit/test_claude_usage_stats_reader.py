import json

import claude_usage_stats_reader

SAMPLE_STATS_CACHE = {
    "firstSessionDate": "2026-05-26T16:44:20.085Z",
    "lastComputedDate": "2026-06-17",
    "dailyModelTokens": [
        {"date": "2026-06-16", "tokensByModel": {"claude-opus-4-8": 1200}},
        {
            "date": "2026-06-17",
            "tokensByModel": {"claude-opus-4-8": 3400, "claude-haiku-4-5": 90},
        },
    ],
    "dailyActivity": [
        {
            "date": "2026-06-17",
            "messageCount": 42,
            "sessionCount": 5,
            "toolCallCount": 130,
        }
    ],
    "modelUsage": {
        "claude-opus-4-8": {
            "inputTokens": 22874565,
            "outputTokens": 118586625,
            "cacheReadInputTokens": 15970324893,
            "cacheCreationInputTokens": 919143720,
            "costUSD": 1234.5,
        }
    },
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


class TestSummarizeStatsCache:
    def test_empty_stats_cache_summarizes_to_empty_series(self):
        summary = claude_usage_stats_reader.summarize_stats_cache({})
        assert summary["stats_first_session_date"] is None
        assert summary["stats_last_computed_date"] is None
        assert summary["daily_model_tokens"] == []
        assert summary["daily_activity"] == []
        assert summary["model_usage_totals"] == {}

    def test_first_session_date_is_truncated_to_calendar_date(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["stats_first_session_date"] == "2026-05-26"

    def test_daily_model_tokens_are_renamed_and_copied(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["daily_model_tokens"][1] == {
            "date": "2026-06-17",
            "tokens_by_model": {"claude-opus-4-8": 3400, "claude-haiku-4-5": 90},
        }

    def test_daily_activity_keys_are_snake_cased(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        assert summary["daily_activity"][0] == {
            "date": "2026-06-17",
            "message_count": 42,
            "session_count": 5,
            "tool_call_count": 130,
        }

    def test_model_usage_totals_expose_cache_read_split(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(SAMPLE_STATS_CACHE)
        opus_totals = summary["model_usage_totals"]["claude-opus-4-8"]
        assert opus_totals["cache_read_input_tokens"] == 15970324893
        assert opus_totals["input_tokens"] == 22874565
        assert opus_totals["output_tokens"] == 118586625
        assert opus_totals["cache_creation_input_tokens"] == 919143720
        assert opus_totals["cost_usd"] == 1234.5

    def test_missing_model_usage_fields_default_to_zero(self):
        summary = claude_usage_stats_reader.summarize_stats_cache(
            {"modelUsage": {"claude-opus-4-8": {}}}
        )
        assert summary["model_usage_totals"]["claude-opus-4-8"] == {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cost_usd": 0,
        }
