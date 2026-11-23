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
    @pytest.mark.parametrize("unmeasured_value", [None, {}, "0"])
    def test_refuses_a_daily_activity_that_is_not_a_list(self, unmeasured_value):
        with pytest.raises(IngestionRefusedError, match="daily_activity"):
            build_claude_usage_payload(
                build_usage_document(daily_activity=unmeasured_value)
            )

    def test_refuses_a_day_whose_counter_is_null(self):
        null_day = {**MEASURED_DAY, "tool_call_count": None}

        with pytest.raises(IngestionRefusedError, match="tool_call_count"):
            build_claude_usage_payload(build_usage_document(daily_activity=[null_day]))


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
