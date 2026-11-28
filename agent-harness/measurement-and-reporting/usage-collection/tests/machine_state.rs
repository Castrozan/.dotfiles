use claude_usage_collector::machine_state::{
    DailyActivity, account_label, current_account_uuid, machine_label,
    summarize_otel_metrics_documents, summarize_stats_cache,
};
use serde_json::{Map, Value, json};

#[test]
fn derives_the_same_opaque_labels_the_published_history_uses() {
    assert_eq!(
        account_label("00000000-1111-2222-3333-444444444444"),
        "bf2fea6531d9"
    );
    assert_eq!(machine_label("nixos"), "44311640c9af");
}

#[test]
fn reads_the_signed_in_account_and_ignores_unusable_configs() {
    let directory = tempfile::tempdir().unwrap();
    let config = directory.path().join(".claude.json");
    std::fs::write(&config, r#"{"oauthAccount":{"accountUuid":"abc"}}"#).unwrap();
    assert_eq!(current_account_uuid(&config).as_deref(), Some("abc"));
    for unusable in [r#"{"oauthAccount":{"accountUuid":""}}"#, "{}", "not json"] {
        std::fs::write(&config, unusable).unwrap();
        assert_eq!(current_account_uuid(&config), None, "{unusable}");
    }
    assert_eq!(
        current_account_uuid(&directory.path().join("missing.json")),
        None
    );
}

fn stats_cache(document: Value) -> Map<String, Value> {
    document.as_object().unwrap().clone()
}

#[test]
fn summarizes_measured_daily_activity_from_the_stats_cache() {
    let summary = summarize_stats_cache(&stats_cache(json!({
        "firstSessionDate": "2026-01-05T08:00:00.000Z",
        "lastComputedDate": "2026-11-26",
        "dailyActivity": [{"date": "2026-11-26", "messageCount": 4, "sessionCount": 1, "toolCallCount": 9}]
    })));
    assert_eq!(summary.first_session_date.as_deref(), Some("2026-01-05"));
    assert_eq!(
        summary.activity_last_computed_date.as_deref(),
        Some("2026-11-26")
    );
    assert_eq!(
        summary.daily_activity,
        Some(vec![DailyActivity {
            date: "2026-11-26".into(),
            message_count: 4,
            session_count: 1,
            tool_call_count: 9
        }])
    );
}

#[test]
fn withholds_daily_activity_when_any_day_was_not_fully_measured() {
    for unmeasured_day in [
        json!({"date": "2026-11-26", "messageCount": 4, "sessionCount": 1}),
        json!({"date": "2026-11-26", "messageCount": -1, "sessionCount": 1, "toolCallCount": 0}),
        json!({"date": "2026-11-26", "messageCount": true, "sessionCount": 1, "toolCallCount": 0}),
        json!({"date": "2026-02-30", "messageCount": 1, "sessionCount": 1, "toolCallCount": 0}),
    ] {
        let summary =
            summarize_stats_cache(&stats_cache(json!({"dailyActivity": [unmeasured_day]})));
        assert_eq!(summary.daily_activity, None);
    }
    assert_eq!(summarize_stats_cache(&Map::new()).daily_activity, None);
    let bad_date = summarize_stats_cache(&stats_cache(json!({"lastComputedDate": "2026-1-5"})));
    assert_eq!(bad_date.activity_last_computed_date, None);
}

fn metric_document(name: &str, temporality: i64, points: Value) -> Value {
    json!({"resourceMetrics": [{"scopeMetrics": [{"metrics": [
        {"name": name, "sum": {"aggregationTemporality": temporality, "dataPoints": points}}
    ]}]}]})
}

#[test]
fn keeps_the_latest_cumulative_point_and_sums_delta_points() {
    let token_point = |value: &str| json!([{"asInt": value, "attributes": [{"key": "type", "value": {"stringValue": "input"}}]}]);
    let documents = vec![
        metric_document("claude_code.token.usage", 2, token_point("100")),
        metric_document("claude_code.token.usage", 2, token_point("250")),
        metric_document("claude_code.cost.usage", 1, json!([{"asDouble": 0.10004}])),
        metric_document("claude_code.cost.usage", 1, json!([{"asDouble": 0.2}])),
    ];
    let summary = summarize_otel_metrics_documents(&documents);
    assert_eq!(summary.token_usage_by_type.get("input"), Some(&250));
    assert_eq!(summary.total_cost_usd, 0.3);
    assert!(summary.has_data);
    assert!(!summarize_otel_metrics_documents(&[]).has_data);
}
