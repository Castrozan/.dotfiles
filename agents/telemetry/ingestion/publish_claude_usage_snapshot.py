import sys
from datetime import datetime, timezone

from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    run_snapshot_publisher,
)

CLAUDE_USAGE_TOPIC = "claude-usage"
CLAUDE_USAGE_SCHEMA_VERSION = 1
DEFAULT_PRODUCER_LABEL = "dotfiles-usage-exporter"
MISSING_DOCUMENT_ARGUMENT_EXIT_CODE = 2
BARE_CALENDAR_DATE_FORMAT = "%Y-%m-%d"
COST_DECIMAL_PLACES = 6


def read_required_snapshot_field(usage_document, field_name, purpose):
    field_value = usage_document.get(field_name)
    if not field_value:
        raise IngestionRefusedError(f"{field_name} must {purpose}")
    return field_value


def stamp_bare_calendar_date_as_utc_midnight(calendar_date):
    computed_at = datetime.strptime(calendar_date, BARE_CALENDAR_DATE_FORMAT).replace(
        tzinfo=timezone.utc
    )
    return computed_at.isoformat().replace("+00:00", "Z")


def build_model_totals(model_name, model_document):
    return {
        "model": model_name,
        "inputTokens": int(model_document["input_tokens"]),
        "outputTokens": int(model_document["output_tokens"]),
        "cacheReadInputTokens": int(model_document["cache_read_input_tokens"]),
        "cacheCreationInputTokens": int(model_document["cache_creation_input_tokens"]),
        "costUsd": float(model_document["cost_usd"]),
    }


def build_model_totals_ordered_by_model_name(model_usage_totals):
    return [
        build_model_totals(model_name, model_usage_totals[model_name])
        for model_name in sorted(model_usage_totals)
    ]


def count_work_recorded_on_the_day(daily_entry):
    return (
        int(daily_entry["message_count"])
        + int(daily_entry["session_count"])
        + int(daily_entry["tool_call_count"])
    )


def build_activity_summary(daily_activity):
    return {
        "activeDayCount": sum(
            1
            for daily_entry in daily_activity
            if count_work_recorded_on_the_day(daily_entry) > 0
        ),
        "messageCount": sum(
            int(daily_entry["message_count"]) for daily_entry in daily_activity
        ),
        "sessionCount": sum(
            int(daily_entry["session_count"]) for daily_entry in daily_activity
        ),
        "toolCallCount": sum(
            int(daily_entry["tool_call_count"]) for daily_entry in daily_activity
        ),
    }


def build_claude_usage_payload(usage_document, environment=None):
    models = build_model_totals_ordered_by_model_name(
        usage_document.get("model_usage_totals", {})
    )
    return {
        "recordedAt": stamp_bare_calendar_date_as_utc_midnight(
            read_required_snapshot_field(
                usage_document,
                "stats_last_computed_date",
                "date the usage statistics the snapshot reports",
            )
        ),
        "accountLabel": read_required_snapshot_field(
            usage_document,
            "account_label",
            "identify the account the reported usage belongs to",
        ),
        "machineLabel": read_required_snapshot_field(
            usage_document,
            "machine_label",
            "identify the machine the reported usage was measured on",
        ),
        "models": models,
        "totalCostUsd": round(
            sum(model_totals["costUsd"] for model_totals in models),
            COST_DECIMAL_PLACES,
        ),
        "activity": build_activity_summary(usage_document.get("daily_activity", [])),
    }


def main(command_line_arguments):
    if not command_line_arguments:
        print(
            "the usage snapshot path must be given because the exporter names its "
            "file after the account and machine labels of the machine it ran on",
            file=sys.stderr,
        )
        return MISSING_DOCUMENT_ARGUMENT_EXIT_CODE
    return run_snapshot_publisher(
        CLAUDE_USAGE_TOPIC,
        CLAUDE_USAGE_SCHEMA_VERSION,
        DEFAULT_PRODUCER_LABEL,
        build_claude_usage_payload,
        command_line_arguments[0],
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
