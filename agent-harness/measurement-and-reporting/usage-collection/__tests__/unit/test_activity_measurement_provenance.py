import pytest

from claude_usage_stats_reader import summarize_stats_cache


@pytest.mark.parametrize(
    "daily_activity",
    [None, {}, [{"date": "2026-07-30", "messageCount": 1, "sessionCount": 1}]],
)
def test_unmeasured_activity_is_absent_not_a_measured_zero(daily_activity):
    cache = {"lastComputedDate": "2026-07-30", "dailyActivity": daily_activity}
    assert "daily_activity" not in summarize_stats_cache(cache)


def test_missing_activity_is_absent_but_explicitly_measured_empty_is_zero():
    assert "daily_activity" not in summarize_stats_cache({})
    assert (
        summarize_stats_cache({"dailyActivity": [], "lastComputedDate": "2026-07-30"})[
            "daily_activity"
        ]
        == []
    )


def test_partially_unmeasured_activity_is_not_silently_reported_as_complete():
    measured = {
        "date": "2026-07-29",
        "messageCount": 1,
        "sessionCount": 1,
        "toolCallCount": 1,
    }
    unknown = {"date": "2026-07-30", "messageCount": 2, "sessionCount": 1}
    assert "daily_activity" not in summarize_stats_cache(
        {"dailyActivity": [measured, unknown]}
    )
