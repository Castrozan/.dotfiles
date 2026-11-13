import itertools

import pytest

from ingestion_snapshot_publisher import IngestionRefusedError
from publish_claude_usage_snapshot import build_claude_usage_payload

MEASURED_DAY = {
    "date": "2026-07-24",
    "message_count": 12,
    "session_count": 2,
    "tool_call_count": 40,
}
EMPTY_DAY = {
    "date": "2026-07-25",
    "message_count": 0,
    "session_count": 0,
    "tool_call_count": 0,
}


def build_usage_document(**overrides):
    usage_document = {
        "stats_last_computed_date": "2026-07-25",
        "account_label": "account-a1b2c3",
        "machine_label": "kira",
        "model_usage_totals": {},
        "daily_activity": [MEASURED_DAY, EMPTY_DAY],
    }
    usage_document.update(overrides)
    return usage_document


class TestActivityIsRefusedWhenItWasNotMeasured:
    def test_refuses_a_document_with_no_daily_activity_key(self):
        usage_document = build_usage_document()
        del usage_document["daily_activity"]

        with pytest.raises(IngestionRefusedError, match="daily_activity"):
            build_claude_usage_payload(usage_document)

    @pytest.mark.parametrize("unmeasured_value", [None, {}, "0"])
    def test_refuses_a_daily_activity_that_is_not_a_list(self, unmeasured_value):
        with pytest.raises(IngestionRefusedError, match="daily_activity"):
            build_claude_usage_payload(
                build_usage_document(daily_activity=unmeasured_value)
            )

    @pytest.mark.parametrize(
        "missing_counter_name",
        ["message_count", "session_count", "tool_call_count"],
    )
    def test_refuses_a_day_whose_counter_was_not_measured(self, missing_counter_name):
        unmeasured_day = {
            key: value
            for key, value in MEASURED_DAY.items()
            if key != missing_counter_name
        }

        with pytest.raises(IngestionRefusedError, match=missing_counter_name):
            build_claude_usage_payload(
                build_usage_document(daily_activity=[unmeasured_day])
            )

    def test_refuses_a_day_whose_counter_is_null(self):
        null_day = {**MEASURED_DAY, "tool_call_count": None}

        with pytest.raises(IngestionRefusedError, match="tool_call_count"):
            build_claude_usage_payload(build_usage_document(daily_activity=[null_day]))


class TestAnExplicitlyMeasuredEmptyListMeansZeroActivity:
    def test_reports_zero_activity_for_a_measured_empty_list(self):
        payload = build_claude_usage_payload(build_usage_document(daily_activity=[]))

        assert payload["activity"] == {
            "activeDayCount": 0,
            "messageCount": 0,
            "sessionCount": 0,
            "toolCallCount": 0,
        }


class TestActivitySummaryIsExhaustiveOverOneDayAndOrderIndependent:
    COUNTER_VALUES = (0, 1, 2)

    def test_every_single_day_counter_combination_is_summarized_by_its_counters(self):
        for message_count, session_count, tool_call_count in itertools.product(
            self.COUNTER_VALUES, repeat=3
        ):
            day = {
                "date": "2026-07-24",
                "message_count": message_count,
                "session_count": session_count,
                "tool_call_count": tool_call_count,
            }

            activity = build_claude_usage_payload(
                build_usage_document(daily_activity=[day])
            )["activity"]

            assert activity == {
                "activeDayCount": int(
                    message_count + session_count + tool_call_count > 0
                ),
                "messageCount": message_count,
                "sessionCount": session_count,
                "toolCallCount": tool_call_count,
            }

    def test_the_activity_summary_does_not_depend_on_the_order_of_days(self):
        days = [
            MEASURED_DAY,
            EMPTY_DAY,
            {
                "date": "2026-07-20",
                "message_count": 3,
                "session_count": 0,
                "tool_call_count": 1,
            },
        ]
        reference_activity = build_claude_usage_payload(
            build_usage_document(daily_activity=days)
        )["activity"]

        for ordering in itertools.permutations(days):
            activity = build_claude_usage_payload(
                build_usage_document(daily_activity=list(ordering))
            )["activity"]

            assert activity == reference_activity
        assert reference_activity == {
            "activeDayCount": 2,
            "messageCount": 15,
            "sessionCount": 2,
            "toolCallCount": 41,
        }
