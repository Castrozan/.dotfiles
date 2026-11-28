use std::path::Path;

use anyhow::Result;
use rusqlite::Connection;

use super::entry_store::record_entry;
use crate::pricing::PricingTable;
use crate::transcript::{UsageEntry, parse_usage_entry, read_complete_lines_from};

pub struct AppendedEntries {
    pub consumed_bytes: u64,
    pub recorded_entries: u64,
}

struct EntryRecorder<'a> {
    connection: &'a Connection,
    pricing: &'a PricingTable,
    recorded_entries: u64,
    failure: Option<rusqlite::Error>,
}

impl EntryRecorder<'_> {
    fn record_line(&mut self, line: &str) {
        if self.failure.is_some() {
            return;
        }
        if let Some(entry) = parse_usage_entry(line) {
            self.record(&entry);
        }
    }

    fn record(&mut self, entry: &UsageEntry) {
        let cost_usd = self.pricing.usage_cost_usd(
            &entry.model,
            entry.is_fast,
            &entry.tokens,
            entry.reported_cost_usd,
        );
        match record_entry(self.connection, entry, cost_usd) {
            Ok(recorded) => self.recorded_entries += u64::from(recorded),
            Err(failure) => self.failure = Some(failure),
        }
    }
}

pub fn record_appended_entries(
    connection: &Connection,
    path: &Path,
    start_offset: u64,
    pricing: &PricingTable,
) -> Result<AppendedEntries> {
    let mut recorder = EntryRecorder {
        connection,
        pricing,
        recorded_entries: 0,
        failure: None,
    };
    let consumed_bytes =
        read_complete_lines_from(path, start_offset, |line| recorder.record_line(line))?;
    match recorder.failure {
        Some(failure) => Err(failure.into()),
        None => Ok(AppendedEntries {
            consumed_bytes,
            recorded_entries: recorder.recorded_entries,
        }),
    }
}
