use serde_json::{Map, Value, json};

use super::{MODEL_USAGE_SOURCE, UsageSnapshot};
use crate::machine_state::DailyActivity;
use crate::usage_totals::ModelUsageTotals;

const RAW_SNAPSHOT_SCHEMA_VERSION: u64 = 1;
const RAW_SNAPSHOT_OBJECT_KEY_PREFIX: &str = "snapshots/";

impl UsageSnapshot {
    pub fn raw_object_key(&self) -> String {
        format!(
            "{RAW_SNAPSHOT_OBJECT_KEY_PREFIX}{}-{}.json",
            self.account_label, self.machine_label
        )
    }

    pub fn encoded_raw_document(&self) -> Vec<u8> {
        let mut encoded = serde_json::to_vec_pretty(&self.raw_document())
            .expect("a JSON value always serializes");
        encoded.push(b'\n');
        encoded
    }

    pub fn raw_document(&self) -> Value {
        let mut document = Map::new();
        document.insert("schema_version".into(), json!(RAW_SNAPSHOT_SCHEMA_VERSION));
        document.insert("account_label".into(), json!(self.account_label));
        document.insert("machine_label".into(), json!(self.machine_label));
        document.insert(
            "stats_first_session_date".into(),
            json!(self.stats_cache.first_session_date),
        );
        document.insert(
            "activity_last_computed_date".into(),
            json!(self.stats_cache.activity_last_computed_date),
        );
        if let Some(daily_activity) = &self.stats_cache.daily_activity {
            document.insert(
                "daily_activity".into(),
                daily_activity.iter().map(daily_activity_document).collect(),
            );
        }
        document.insert(
            "model_usage_totals".into(),
            self.model_usage_totals()
                .iter()
                .map(|(model, totals)| (model.clone(), model_totals_document(totals)))
                .collect::<Map<_, _>>()
                .into(),
        );
        document.insert(
            "daily_model_tokens".into(),
            self.tokens_by_model_per_day()
                .into_iter()
                .map(|(date, tokens_by_model)| {
                    json!({"date": date, "tokens_by_model": tokens_by_model})
                })
                .collect(),
        );
        document.insert(
            "stats_last_computed_date".into(),
            json!(self.last_usage_date()),
        );
        document.insert(
            "model_usage_first_date".into(),
            json!(self.first_usage_date()),
        );
        document.insert("model_usage_source".into(), json!(MODEL_USAGE_SOURCE));
        document.insert("captured_at_utc".into(), json!(self.captured_at_utc));
        document.insert(
            "otel_metrics".into(),
            json!({
                "token_usage_by_type": self.otel_metrics.token_usage_by_type,
                "total_cost_usd": self.otel_metrics.total_cost_usd,
                "has_data": self.otel_metrics.has_data,
            }),
        );
        Value::Object(document)
    }
}

fn daily_activity_document(daily_activity: &DailyActivity) -> Value {
    json!({
        "date": daily_activity.date,
        "message_count": daily_activity.message_count,
        "session_count": daily_activity.session_count,
        "tool_call_count": daily_activity.tool_call_count,
    })
}

fn model_totals_document(totals: &ModelUsageTotals) -> Value {
    json!({
        "input_tokens": totals.input_tokens,
        "output_tokens": totals.output_tokens,
        "cache_read_input_tokens": totals.cache_read_input_tokens,
        "cache_creation_input_tokens": totals.cache_creation_input_tokens,
        "cost_usd": totals.cost_usd,
    })
}
