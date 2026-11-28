mod ingestion_payload;
mod raw_document;

use std::collections::BTreeMap;

use crate::machine_state::{OtelMetricsSummary, StatsCacheSummary};
use crate::usage_totals::{DailyModelUsage, ModelUsageTotals};

pub const MODEL_USAGE_SOURCE: &str = "claude-transcript-ledger";

#[derive(Debug, Clone, PartialEq)]
pub struct UsageSnapshot {
    pub account_label: String,
    pub machine_label: String,
    pub captured_at_utc: String,
    pub stats_cache: StatsCacheSummary,
    pub daily_model_usage: Vec<DailyModelUsage>,
    pub otel_metrics: OtelMetricsSummary,
}

impl UsageSnapshot {
    pub fn model_usage_totals(&self) -> BTreeMap<String, ModelUsageTotals> {
        let mut totals_by_model: BTreeMap<String, ModelUsageTotals> = BTreeMap::new();
        for daily_usage in &self.daily_model_usage {
            totals_by_model
                .entry(daily_usage.model_label())
                .or_default()
                .add(&daily_usage.totals);
        }
        totals_by_model
    }

    pub fn first_usage_date(&self) -> Option<&str> {
        self.daily_model_usage
            .iter()
            .map(|usage| usage.usage_date.as_str())
            .min()
    }

    pub fn last_usage_date(&self) -> Option<&str> {
        self.daily_model_usage
            .iter()
            .map(|usage| usage.usage_date.as_str())
            .max()
    }

    pub fn tokens_by_model_per_day(&self) -> BTreeMap<&str, BTreeMap<String, u64>> {
        let mut tokens_per_day: BTreeMap<&str, BTreeMap<String, u64>> = BTreeMap::new();
        for daily_usage in &self.daily_model_usage {
            *tokens_per_day
                .entry(daily_usage.usage_date.as_str())
                .or_default()
                .entry(daily_usage.model_label())
                .or_insert(0) += daily_usage.totals.token_total();
        }
        tokens_per_day
    }
}
