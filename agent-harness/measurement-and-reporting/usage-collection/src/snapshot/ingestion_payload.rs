use anyhow::{Result, anyhow};
use serde_json::{Value, json};

use super::UsageSnapshot;
use crate::machine_state::DailyActivity;

const COST_DECIMAL_PLACES: i32 = 6;

impl UsageSnapshot {
    pub fn ingestion_payload(&self) -> Result<Value> {
        let last_usage_date = self.last_usage_date().ok_or_else(|| {
            anyhow!("stats_last_computed_date must date the usage statistics the snapshot reports")
        })?;
        let daily_activity = self.stats_cache.daily_activity.as_deref().ok_or_else(|| {
            anyhow!("daily_activity must list the activity measured on the machine")
        })?;
        let models: Vec<Value> = self
            .model_usage_totals()
            .iter()
            .map(|(model, totals)| {
                json!({
                    "model": model,
                    "inputTokens": totals.input_tokens,
                    "outputTokens": totals.output_tokens,
                    "cacheReadInputTokens": totals.cache_read_input_tokens,
                    "cacheCreationInputTokens": totals.cache_creation_input_tokens,
                    "costUsd": totals.cost_usd,
                })
            })
            .collect();
        let total_cost_usd: f64 = self
            .model_usage_totals()
            .values()
            .map(|totals| totals.cost_usd)
            .sum();
        Ok(json!({
            "recordedAt": format!("{last_usage_date}T00:00:00Z"),
            "accountLabel": self.account_label,
            "machineLabel": self.machine_label,
            "models": models,
            "totalCostUsd": round_to_decimal_places(total_cost_usd, COST_DECIMAL_PLACES),
            "activity": activity_summary(daily_activity),
        }))
    }
}

fn activity_summary(daily_activity: &[DailyActivity]) -> Value {
    json!({
        "activeDayCount": daily_activity.iter().filter(|day| day.recorded_work() > 0).count(),
        "messageCount": daily_activity.iter().map(|day| day.message_count).sum::<u64>(),
        "sessionCount": daily_activity.iter().map(|day| day.session_count).sum::<u64>(),
        "toolCallCount": daily_activity.iter().map(|day| day.tool_call_count).sum::<u64>(),
    })
}

fn round_to_decimal_places(value: f64, decimal_places: i32) -> f64 {
    let scale = 10f64.powi(decimal_places);
    (value * scale).round() / scale
}
