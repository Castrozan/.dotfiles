import pytest

from ingestion_snapshot_publisher import IngestionRefusedError
from publish_claude_usage_snapshot import (
    CLAUDE_USAGE_SCHEMA_VERSION,
    CLAUDE_USAGE_TOPIC,
    build_claude_usage_payload,
)

LAPTOP_ENVIRONMENT = {}

USAGE_SNAPSHOT_DOCUMENT = {
    "schema_version": 1,
    "account_label": "2c9c0c7cb164",
    "machine_label": "71fc83e765e0",
    "stats_first_session_date": "2026-05-26",
    "stats_last_computed_date": "2026-06-17",
    "model_usage_totals": {
        "gpt-5.6-sol": {
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 4226549,
            "cost_usd": 0.25,
            "input_tokens": 3065,
            "output_tokens": 101746,
        },
        "claude-opus-4-8": {
            "cache_creation_input_tokens": 919143720,
            "cache_read_input_tokens": 15970324893,
            "cost_usd": 132.5,
            "input_tokens": 22874565,
            "output_tokens": 118586625,
        },
    },
    "daily_activity": [
        {
            "date": "2026-05-26",
            "message_count": 1407,
            "session_count": 2,
            "tool_call_count": 281,
        },
        {
            "date": "2026-05-28",
            "message_count": 1578,
            "session_count": 1,
            "tool_call_count": 420,
        },
        {
            "date": "2026-06-17",
            "message_count": 0,
            "session_count": 0,
            "tool_call_count": 0,
        },
    ],
    "daily_model_tokens": {"2026-05-26": {"claude-opus-4-8": 4096}},
    "memory_recall_savings": {"recalled_memory_count": 12},
    "otel_metrics": {"exported": False},
}


class TestUsageSnapshotIsMappedOntoTheContractPayload:
    def test_names_the_topic_and_schema_version_the_api_serves(self):
        assert CLAUDE_USAGE_TOPIC == "claude-usage"
        assert CLAUDE_USAGE_SCHEMA_VERSION == 1

    def test_stamps_the_bare_computed_date_as_the_utc_midnight_it_stands_for(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert payload["recordedAt"] == "2026-06-17T00:00:00Z"

    def test_carries_the_labels_that_identify_the_account_and_the_machine(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert payload["accountLabel"] == "2c9c0c7cb164"
        assert payload["machineLabel"] == "71fc83e765e0"

    def test_turns_the_model_keyed_totals_into_a_list_ordered_by_model_name(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert [entry["model"] for entry in payload["models"]] == [
            "claude-opus-4-8",
            "gpt-5.6-sol",
        ]

    def test_renames_the_snake_case_token_counters_the_snapshot_writes(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )
        opus = payload["models"][0]

        assert opus["inputTokens"] == 22874565
        assert opus["outputTokens"] == 118586625
        assert opus["cacheReadInputTokens"] == 15970324893
        assert opus["cacheCreationInputTokens"] == 919143720
        assert opus["costUsd"] == 132.5

    def test_totals_the_spend_the_per_model_costs_add_up_to(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert payload["totalCostUsd"] == 132.75

    def test_sums_the_daily_activity_into_the_counts_the_contract_carries(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert payload["activity"]["messageCount"] == 2985
        assert payload["activity"]["sessionCount"] == 3
        assert payload["activity"]["toolCallCount"] == 701

    def test_counts_only_the_days_that_recorded_work_as_active(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert payload["activity"]["activeDayCount"] == 2

    def test_emits_no_key_the_contract_does_not_declare(self):
        payload = build_claude_usage_payload(
            USAGE_SNAPSHOT_DOCUMENT, LAPTOP_ENVIRONMENT
        )

        assert set(payload) == {
            "recordedAt",
            "accountLabel",
            "machineLabel",
            "models",
            "totalCostUsd",
            "activity",
        }
        assert set(payload["models"][0]) == {
            "model",
            "inputTokens",
            "outputTokens",
            "cacheReadInputTokens",
            "cacheCreationInputTokens",
            "costUsd",
        }
        assert set(payload["activity"]) == {
            "activeDayCount",
            "messageCount",
            "sessionCount",
            "toolCallCount",
        }


class TestAMachineThatHasNotBeenUsedYetStillIngests:
    def test_reports_an_empty_model_list_and_a_silent_activity_summary(self):
        document = {
            **USAGE_SNAPSHOT_DOCUMENT,
            "model_usage_totals": {},
            "daily_activity": [],
        }

        payload = build_claude_usage_payload(document, LAPTOP_ENVIRONMENT)

        assert payload["models"] == []
        assert payload["totalCostUsd"] == 0
        assert payload["activity"] == {
            "activeDayCount": 0,
            "messageCount": 0,
            "sessionCount": 0,
            "toolCallCount": 0,
        }


class TestSnapshotsMissingTheirIdentityAreRefusedRatherThanGuessed:
    def test_refuses_a_snapshot_that_does_not_say_when_it_was_computed(self):
        document = {
            key: value
            for key, value in USAGE_SNAPSHOT_DOCUMENT.items()
            if key != "stats_last_computed_date"
        }

        with pytest.raises(IngestionRefusedError, match="stats_last_computed_date"):
            build_claude_usage_payload(document, LAPTOP_ENVIRONMENT)

    def test_refuses_a_snapshot_that_does_not_name_the_machine_it_measured(self):
        document = {**USAGE_SNAPSHOT_DOCUMENT, "machine_label": ""}

        with pytest.raises(IngestionRefusedError, match="machine_label"):
            build_claude_usage_payload(document, LAPTOP_ENVIRONMENT)

    def test_refuses_a_snapshot_that_does_not_name_the_account_it_measured(self):
        document = {
            key: value
            for key, value in USAGE_SNAPSHOT_DOCUMENT.items()
            if key != "account_label"
        }

        with pytest.raises(IngestionRefusedError, match="account_label"):
            build_claude_usage_payload(document, LAPTOP_ENVIRONMENT)
