use std::collections::{BTreeMap, HashMap};
use std::io::{BufRead, BufReader};
use std::path::Path;

use serde_json::Value;

const TOKEN_USAGE_METRIC_NAME: &str = "claude_code.token.usage";
const COST_USAGE_METRIC_NAME: &str = "claude_code.cost.usage";
const TOKEN_TYPE_ATTRIBUTE_KEY: &str = "type";
const UNKNOWN_TOKEN_TYPE: &str = "unknown";
const DELTA_AGGREGATION_TEMPORALITY: i64 = 1;
const COST_DECIMAL_PLACES: i32 = 4;

#[derive(Debug, Clone, Default, PartialEq)]
pub struct OtelMetricsSummary {
    pub token_usage_by_type: BTreeMap<String, i64>,
    pub total_cost_usd: f64,
    pub has_data: bool,
}

type StreamAttributes = BTreeMap<String, String>;

#[derive(Default)]
struct MetricStreams {
    cumulative_latest: HashMap<StreamAttributes, f64>,
    delta_accumulated: HashMap<StreamAttributes, f64>,
}

impl MetricStreams {
    fn add_metric(&mut self, metric: &Value) {
        let sum = metric.get("sum");
        let is_delta = sum
            .and_then(|sum| sum.get("aggregationTemporality"))
            .and_then(Value::as_i64)
            == Some(DELTA_AGGREGATION_TEMPORALITY);
        for data_point in array_at(sum, "dataPoints") {
            let attributes = data_point_attributes(data_point);
            let value = data_point_value(data_point);
            if is_delta {
                *self.delta_accumulated.entry(attributes).or_insert(0.0) += value;
            } else {
                self.cumulative_latest.insert(attributes, value);
            }
        }
    }

    fn reduced(self) -> impl Iterator<Item = (StreamAttributes, f64)> {
        self.cumulative_latest
            .into_iter()
            .chain(self.delta_accumulated)
    }
}

#[derive(Default)]
struct OtelMetricsAccumulator {
    token_usage: MetricStreams,
    cost_usage: MetricStreams,
}

impl OtelMetricsAccumulator {
    fn add_document(&mut self, document: &Value) {
        let metrics = array_at(Some(document), "resourceMetrics")
            .iter()
            .flat_map(|resource_metrics| array_at(Some(resource_metrics), "scopeMetrics"))
            .flat_map(|scope_metrics| array_at(Some(scope_metrics), "metrics"));
        for metric in metrics {
            match metric.get("name").and_then(Value::as_str) {
                Some(TOKEN_USAGE_METRIC_NAME) => self.token_usage.add_metric(metric),
                Some(COST_USAGE_METRIC_NAME) => self.cost_usage.add_metric(metric),
                _ => {}
            }
        }
    }

    fn summary(self) -> OtelMetricsSummary {
        let mut token_usage_by_type = BTreeMap::new();
        for (attributes, value) in self.token_usage.reduced() {
            let token_type = attributes
                .get(TOKEN_TYPE_ATTRIBUTE_KEY)
                .cloned()
                .unwrap_or_else(|| UNKNOWN_TOKEN_TYPE.to_string());
            *token_usage_by_type.entry(token_type).or_insert(0) += value.trunc() as i64;
        }
        let cost_sum: f64 = self.cost_usage.reduced().map(|(_, value)| value).sum();
        let scale = 10f64.powi(COST_DECIMAL_PLACES);
        let total_cost_usd = (cost_sum * scale).round() / scale;
        OtelMetricsSummary {
            has_data: !token_usage_by_type.is_empty() || total_cost_usd > 0.0,
            token_usage_by_type,
            total_cost_usd,
        }
    }
}

pub fn summarize_otel_metrics_file(metrics_file_path: &Path) -> OtelMetricsSummary {
    let mut accumulator = OtelMetricsAccumulator::default();
    if let Ok(metrics_file) = std::fs::File::open(metrics_file_path) {
        for line in BufReader::new(metrics_file).lines().map_while(Result::ok) {
            if let Ok(document) = serde_json::from_str::<Value>(line.trim()) {
                accumulator.add_document(&document);
            }
        }
    }
    accumulator.summary()
}

pub fn summarize_otel_metrics_documents(documents: &[Value]) -> OtelMetricsSummary {
    let mut accumulator = OtelMetricsAccumulator::default();
    documents
        .iter()
        .for_each(|document| accumulator.add_document(document));
    accumulator.summary()
}

fn array_at<'a>(container: Option<&'a Value>, field: &str) -> &'a [Value] {
    container
        .and_then(|container| container.get(field))
        .and_then(Value::as_array)
        .map_or(&[], Vec::as_slice)
}

fn data_point_attributes(data_point: &Value) -> StreamAttributes {
    array_at(Some(data_point), "attributes")
        .iter()
        .filter_map(|attribute| {
            let key = attribute.get("key")?.as_str()?.to_string();
            Some((key, attribute_text(attribute.get("value"))))
        })
        .collect()
}

fn attribute_text(attribute_value: Option<&Value>) -> String {
    ["stringValue", "intValue", "doubleValue", "boolValue"]
        .iter()
        .find_map(|value_key| attribute_value?.get(*value_key))
        .map(|value| match value {
            Value::String(text) => text.clone(),
            other => other.to_string(),
        })
        .unwrap_or_default()
}

fn data_point_value(data_point: &Value) -> f64 {
    ["asInt", "asDouble"]
        .iter()
        .find_map(|value_key| data_point.get(*value_key))
        .and_then(|value| match value {
            Value::String(text) => text.parse().ok(),
            other => other.as_f64(),
        })
        .unwrap_or(0.0)
}
