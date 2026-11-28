use chrono::{DateTime, Utc};

use super::line_shape::{MessageUsage, TranscriptLine, UsageRecord};

const USAGE_OBJECT_MARKER: &str = "\"usage\":{";
const SYNTHETIC_MODEL: &str = "<synthetic>";
const FAST_SPEED: &str = "fast";
const FAST_MODEL_LABEL_SUFFIX: &str = "-fast";

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct TokenCounts {
    pub input: u64,
    pub output: u64,
    pub cache_creation_five_minute: u64,
    pub cache_creation_one_hour: u64,
    pub cache_read: u64,
}

impl TokenCounts {
    pub fn total(&self) -> u64 {
        self.input + self.output + self.cache_creation() + self.cache_read
    }

    pub fn cache_creation(&self) -> u64 {
        self.cache_creation_five_minute + self.cache_creation_one_hour
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct MessageIdentity {
    pub message_id: String,
    pub request_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct UsageEntry {
    pub identity: Option<MessageIdentity>,
    pub is_sidechain: bool,
    pub usage_date: String,
    pub model: String,
    pub is_fast: bool,
    pub tokens: TokenCounts,
    pub reported_cost_usd: Option<f64>,
}

impl UsageEntry {
    pub fn model_label(&self) -> String {
        model_label(&self.model, self.is_fast)
    }
}

pub fn model_label(model: &str, is_fast: bool) -> String {
    if is_fast {
        format!("{model}{FAST_MODEL_LABEL_SUFFIX}")
    } else {
        model.to_string()
    }
}

pub fn parse_usage_entry(line: &str) -> Option<UsageEntry> {
    if !line.contains(USAGE_OBJECT_MARKER) {
        return None;
    }
    let transcript_line: TranscriptLine = serde_json::from_str(line).ok()?;
    usage_entry_from_record(transcript_line.into_usage_record()?)
}

fn usage_entry_from_record(record: UsageRecord) -> Option<UsageEntry> {
    let model = billable_model(record.message.model)?;
    let usage_date = utc_calendar_date(&record.timestamp)?;
    Some(UsageEntry {
        identity: message_identity(record.message.id, record.request_id),
        is_sidechain: record.is_sidechain.unwrap_or(false),
        usage_date,
        model,
        is_fast: record.usage.speed.as_deref() == Some(FAST_SPEED),
        tokens: token_counts(&record.usage),
        reported_cost_usd: valid_reported_cost(record.cost_usd),
    })
}

fn billable_model(model: Option<String>) -> Option<String> {
    non_empty(model).filter(|model| model != SYNTHETIC_MODEL)
}

fn message_identity(
    message_id: Option<String>,
    request_id: Option<String>,
) -> Option<MessageIdentity> {
    Some(MessageIdentity {
        message_id: non_empty(message_id)?,
        request_id: non_empty(request_id),
    })
}

fn non_empty(text: Option<String>) -> Option<String> {
    text.filter(|text| !text.is_empty())
}

fn valid_reported_cost(cost_usd: Option<f64>) -> Option<f64> {
    cost_usd.filter(|cost| cost.is_finite() && *cost >= 0.0)
}

fn token_counts(usage: &MessageUsage) -> TokenCounts {
    let (cache_creation_five_minute, cache_creation_one_hour) = match &usage.cache_creation {
        Some(breakdown) => (
            breakdown.ephemeral_5m_input_tokens.unwrap_or(0),
            breakdown.ephemeral_1h_input_tokens.unwrap_or(0),
        ),
        None => (usage.cache_creation_input_tokens.unwrap_or(0), 0),
    };
    TokenCounts {
        input: usage.input_tokens,
        output: usage.output_tokens,
        cache_creation_five_minute,
        cache_creation_one_hour,
        cache_read: usage.cache_read_input_tokens.unwrap_or(0),
    }
}

fn utc_calendar_date(timestamp: &str) -> Option<String> {
    let instant = DateTime::parse_from_rfc3339(timestamp).ok()?;
    Some(instant.with_timezone(&Utc).format("%Y-%m-%d").to_string())
}
