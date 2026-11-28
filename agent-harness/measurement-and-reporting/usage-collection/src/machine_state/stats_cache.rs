use std::path::Path;

use chrono::NaiveDate;
use serde_json::{Map, Value};

const CALENDAR_DATE_LENGTH: usize = 10;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DailyActivity {
    pub date: String,
    pub message_count: u64,
    pub session_count: u64,
    pub tool_call_count: u64,
}

impl DailyActivity {
    pub fn recorded_work(&self) -> u64 {
        self.message_count + self.session_count + self.tool_call_count
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct StatsCacheSummary {
    pub first_session_date: Option<String>,
    pub activity_last_computed_date: Option<String>,
    pub daily_activity: Option<Vec<DailyActivity>>,
}

pub fn read_stats_cache_summary(stats_cache_path: &Path) -> StatsCacheSummary {
    let document = std::fs::read(stats_cache_path)
        .ok()
        .and_then(|bytes| serde_json::from_slice::<Map<String, Value>>(&bytes).ok())
        .unwrap_or_default();
    summarize_stats_cache(&document)
}

pub fn summarize_stats_cache(stats_cache: &Map<String, Value>) -> StatsCacheSummary {
    StatsCacheSummary {
        first_session_date: stats_cache
            .get("firstSessionDate")
            .and_then(Value::as_str)
            .map(|first_session| {
                first_session
                    .chars()
                    .take(CALENDAR_DATE_LENGTH)
                    .collect::<String>()
            })
            .filter(|first_session_date| !first_session_date.is_empty()),
        activity_last_computed_date: stats_cache
            .get("lastComputedDate")
            .and_then(Value::as_str)
            .filter(|date| is_canonical_calendar_date(date))
            .map(str::to_string),
        daily_activity: complete_daily_activity(stats_cache.get("dailyActivity")),
    }
}

fn complete_daily_activity(daily_entries: Option<&Value>) -> Option<Vec<DailyActivity>> {
    daily_entries?
        .as_array()?
        .iter()
        .map(measured_daily_activity)
        .collect()
}

fn measured_daily_activity(daily_entry: &Value) -> Option<DailyActivity> {
    let [message_count, session_count, tool_call_count] = daily_counters(
        daily_entry,
        ["messageCount", "sessionCount", "toolCallCount"],
    )?;
    Some(DailyActivity {
        date: canonical_date_field(daily_entry)?,
        message_count,
        session_count,
        tool_call_count,
    })
}

fn canonical_date_field(daily_entry: &Value) -> Option<String> {
    let date = daily_entry.get("date")?.as_str()?;
    is_canonical_calendar_date(date).then(|| date.to_string())
}

fn daily_counters<const COUNT: usize>(
    daily_entry: &Value,
    fields: [&str; COUNT],
) -> Option<[u64; COUNT]> {
    let mut counters = [0u64; COUNT];
    for (counter, field) in counters.iter_mut().zip(fields) {
        *counter = daily_entry.get(field)?.as_u64()?;
    }
    Some(counters)
}

pub fn is_canonical_calendar_date(value: &str) -> bool {
    has_calendar_date_shape(value) && NaiveDate::parse_from_str(value, "%Y-%m-%d").is_ok()
}

fn has_calendar_date_shape(value: &str) -> bool {
    value.len() == CALENDAR_DATE_LENGTH && value.bytes().enumerate().all(calendar_date_byte_matches)
}

fn calendar_date_byte_matches((index, byte): (usize, u8)) -> bool {
    match index {
        4 | 7 => byte == b'-',
        _ => byte.is_ascii_digit(),
    }
}
