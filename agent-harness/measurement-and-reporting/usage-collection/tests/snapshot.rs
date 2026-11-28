use claude_usage_collector::machine_state::{DailyActivity, OtelMetricsSummary, StatsCacheSummary};
use claude_usage_collector::snapshot::{MODEL_USAGE_SOURCE, UsageSnapshot};
use claude_usage_collector::usage_totals::{DailyModelUsage, ModelUsageTotals};
use serde_json::{Value, json};

fn daily_usage(
    date: &str,
    model: &str,
    is_fast: bool,
    input_tokens: u64,
    cost_usd: f64,
) -> DailyModelUsage {
    DailyModelUsage {
        usage_date: date.into(),
        model: model.into(),
        is_fast,
        totals: ModelUsageTotals {
            input_tokens,
            output_tokens: 1,
            cache_read_input_tokens: 2,
            cache_creation_input_tokens: 3,
            cost_usd,
        },
    }
}

fn day(date: &str, message_count: u64) -> DailyActivity {
    DailyActivity {
        date: date.into(),
        message_count,
        session_count: message_count.min(1),
        tool_call_count: 2 * message_count,
    }
}

fn snapshot(daily_activity: Option<Vec<DailyActivity>>) -> UsageSnapshot {
    UsageSnapshot {
        account_label: "bf2fea6531d9".into(),
        machine_label: "44311640c9af".into(),
        captured_at_utc: "2026-11-27T23:00:00.000Z".into(),
        stats_cache: StatsCacheSummary {
            first_session_date: Some("2026-01-05".into()),
            activity_last_computed_date: Some("2026-11-26".into()),
            daily_activity,
        },
        daily_model_usage: vec![
            daily_usage("2026-11-25", "claude-opus-5-5", false, 10, 0.1),
            daily_usage("2026-11-26", "claude-opus-5-5", false, 20, 0.2),
            daily_usage("2026-11-26", "claude-opus-5-5", true, 5, 0.0000004),
        ],
        otel_metrics: OtelMetricsSummary::default(),
    }
}

#[test]
fn normalizes_totals_per_model_label_into_the_ingestion_payload() {
    let payload = snapshot(Some(vec![day("2026-11-25", 3), day("2026-11-26", 0)]))
        .ingestion_payload()
        .unwrap();
    assert_eq!(payload["recordedAt"], json!("2026-11-26T00:00:00Z"));
    assert_eq!(payload["accountLabel"], json!("bf2fea6531d9"));
    let models: Vec<&Value> = payload["models"].as_array().unwrap().iter().collect();
    assert_eq!(models[0]["model"], json!("claude-opus-5-5"));
    assert_eq!(models[0]["inputTokens"], json!(30));
    assert_eq!(models[0]["cacheCreationInputTokens"], json!(6));
    assert_eq!(models[1]["model"], json!("claude-opus-5-5-fast"));
    assert_eq!(payload["totalCostUsd"], json!(0.3));
    assert_eq!(
        payload["activity"],
        json!({"activeDayCount": 1, "messageCount": 3, "sessionCount": 1, "toolCallCount": 6})
    );
}

#[test]
fn refuses_to_publish_activity_that_was_not_measured() {
    let refusal = snapshot(None).ingestion_payload().unwrap_err();
    assert!(refusal.to_string().contains("daily_activity"), "{refusal}");
}

#[test]
fn writes_the_raw_document_with_sorted_keys_and_its_object_key() {
    let usage_snapshot = snapshot(Some(vec![day("2026-11-26", 1)]));
    assert_eq!(
        usage_snapshot.raw_object_key(),
        "snapshots/bf2fea6531d9-44311640c9af.json"
    );
    let encoded = String::from_utf8(usage_snapshot.encoded_raw_document()).unwrap();
    assert!(encoded.ends_with("}\n"));
    let document: Value = serde_json::from_str(&encoded).unwrap();
    let keys: Vec<&String> = document.as_object().unwrap().keys().collect();
    let mut sorted_keys = keys.clone();
    sorted_keys.sort();
    assert_eq!(keys, sorted_keys);
    assert_eq!(document["model_usage_source"], json!(MODEL_USAGE_SOURCE));
    assert_eq!(document["model_usage_first_date"], json!("2026-11-25"));
    assert_eq!(document["stats_last_computed_date"], json!("2026-11-26"));
    assert_eq!(
        document["daily_model_tokens"][1],
        json!({"date": "2026-11-26", "tokens_by_model": {"claude-opus-5-5": 26, "claude-opus-5-5-fast": 11}})
    );
    assert_eq!(
        document["model_usage_totals"]["claude-opus-5-5"]["input_tokens"],
        json!(30)
    );
    assert_eq!(document["daily_activity"][0]["tool_call_count"], json!(2));
}

#[test]
fn omits_daily_activity_from_the_raw_document_when_unmeasured() {
    let document = snapshot(None).raw_document();
    assert!(document.get("daily_activity").is_none());
    assert_eq!(document["stats_first_session_date"], json!("2026-01-05"));
}
