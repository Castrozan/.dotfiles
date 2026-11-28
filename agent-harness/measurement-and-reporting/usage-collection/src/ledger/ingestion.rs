use std::collections::HashMap;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use super::UsageLedger;
use super::entry_store::record_entry;
use crate::pricing::PricingTable;
use crate::transcript::{
    FileIdentity, TranscriptFileState, parse_usage_entry, read_complete_lines_from,
    transcript_file_state,
};

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct IngestionSummary {
    pub changed_transcripts: usize,
    pub recorded_entries: u64,
}

#[derive(Debug, Clone, Copy)]
struct FileCursor {
    identity: FileIdentity,
    consumed_bytes: u64,
}

impl FileCursor {
    fn resume_offset_for(&self, state: &TranscriptFileState) -> u64 {
        if self.identity == state.identity && self.consumed_bytes <= state.length {
            self.consumed_bytes
        } else {
            0
        }
    }

    fn has_consumed_all_of(&self, state: &TranscriptFileState) -> bool {
        self.identity == state.identity && self.consumed_bytes == state.length
    }
}

impl UsageLedger {
    pub fn ingest_transcripts(
        &mut self,
        transcript_paths: &[PathBuf],
        pricing: &PricingTable,
    ) -> Result<IngestionSummary> {
        let cursors = self.file_cursors()?;
        let mut summary = IngestionSummary::default();
        for path in transcript_paths {
            let Some(path_text) = path.to_str() else {
                continue;
            };
            let Ok(state) = transcript_file_state(path) else {
                continue;
            };
            if cursors
                .get(path_text)
                .is_some_and(|cursor| cursor.has_consumed_all_of(&state))
            {
                continue;
            }
            summary.changed_transcripts += 1;
            summary.recorded_entries += self
                .ingest_transcript(path, path_text, pricing)
                .with_context(|| format!("could not ingest {}", path.display()))?;
        }
        Ok(summary)
    }

    fn file_cursors(&self) -> Result<HashMap<String, FileCursor>> {
        let mut statement = self
            .connection
            .prepare("SELECT path, device, inode, consumed_bytes FROM source_file")?;
        let rows = statement.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                FileCursor {
                    identity: FileIdentity {
                        device: row.get::<_, i64>(1)? as u64,
                        inode: row.get::<_, i64>(2)? as u64,
                    },
                    consumed_bytes: row.get::<_, i64>(3)? as u64,
                },
            ))
        })?;
        Ok(rows.collect::<rusqlite::Result<_>>()?)
    }

    fn ingest_transcript(
        &mut self,
        path: &Path,
        path_text: &str,
        pricing: &PricingTable,
    ) -> Result<u64> {
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let state = transcript_file_state(path)?;
        let resume_offset = read_file_cursor(&transaction, path_text)?
            .map_or(0, |cursor| cursor.resume_offset_for(&state));
        let mut recorded_entries = 0;
        let mut recording_failure = None;
        let consumed_bytes = read_complete_lines_from(path, resume_offset, |line| {
            if recording_failure.is_some() {
                return;
            }
            let Some(entry) = parse_usage_entry(line) else {
                return;
            };
            let cost_usd = pricing.usage_cost_usd(
                &entry.model,
                entry.is_fast,
                &entry.tokens,
                entry.reported_cost_usd,
            );
            match record_entry(&transaction, &entry, cost_usd) {
                Ok(true) => recorded_entries += 1,
                Ok(false) => {}
                Err(failure) => recording_failure = Some(failure),
            }
        })?;
        if let Some(failure) = recording_failure {
            return Err(failure.into());
        }
        write_file_cursor(&transaction, path_text, state.identity, consumed_bytes)?;
        transaction.commit()?;
        Ok(recorded_entries)
    }
}

fn read_file_cursor(
    connection: &Connection,
    path_text: &str,
) -> rusqlite::Result<Option<FileCursor>> {
    connection
        .query_row(
            "SELECT device, inode, consumed_bytes FROM source_file WHERE path = ?1",
            [path_text],
            |row| {
                Ok(FileCursor {
                    identity: FileIdentity {
                        device: row.get::<_, i64>(0)? as u64,
                        inode: row.get::<_, i64>(1)? as u64,
                    },
                    consumed_bytes: row.get::<_, i64>(2)? as u64,
                })
            },
        )
        .optional()
}

fn write_file_cursor(
    connection: &Connection,
    path_text: &str,
    identity: FileIdentity,
    consumed_bytes: u64,
) -> rusqlite::Result<()> {
    connection.execute(
        "INSERT INTO source_file (path, device, inode, consumed_bytes) VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT (path) DO UPDATE SET device = excluded.device, inode = excluded.inode,
            consumed_bytes = excluded.consumed_bytes",
        params![
            path_text,
            identity.device as i64,
            identity.inode as i64,
            consumed_bytes as i64
        ],
    )?;
    Ok(())
}
