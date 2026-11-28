use std::collections::HashMap;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use rusqlite::{Connection, OptionalExtension, Row, Transaction, TransactionBehavior, params};

use super::UsageLedger;
use super::entry_recorder::record_appended_entries;
use super::row_columns::integer_columns;
use crate::pricing::PricingTable;
use crate::transcript::{FileIdentity, TranscriptFileState, transcript_file_state};

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
        for (path, path_text) in changed_transcripts(transcript_paths, &cursors) {
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
        let rows = statement.query_map([], source_file_row)?;
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
        let (state, resume_offset) = resume_point(&transaction, path, path_text)?;
        let appended = record_appended_entries(&transaction, path, resume_offset, pricing)?;
        complete_ingestion(
            transaction,
            path_text,
            state.identity,
            appended.consumed_bytes,
        )?;
        Ok(appended.recorded_entries)
    }
}

fn changed_transcripts<'a>(
    transcript_paths: &'a [PathBuf],
    cursors: &'a HashMap<String, FileCursor>,
) -> impl Iterator<Item = (&'a Path, &'a str)> {
    transcript_paths
        .iter()
        .filter_map(|path| Some((path.as_path(), path.to_str()?)))
        .filter(|(path, path_text)| has_unread_bytes(path, cursors.get(*path_text)))
}

fn has_unread_bytes(path: &Path, cursor: Option<&FileCursor>) -> bool {
    match transcript_file_state(path) {
        Ok(state) => !cursor.is_some_and(|cursor| cursor.has_consumed_all_of(&state)),
        Err(_) => false,
    }
}

fn source_file_row(row: &Row<'_>) -> rusqlite::Result<(String, FileCursor)> {
    Ok((row.get(0)?, file_cursor_at(row, 1)?))
}

fn file_cursor_at(row: &Row<'_>, first_column: usize) -> rusqlite::Result<FileCursor> {
    let [device, inode, consumed_bytes] = integer_columns::<3>(row, first_column)?;
    Ok(FileCursor {
        identity: FileIdentity { device, inode },
        consumed_bytes,
    })
}

fn resume_point(
    connection: &Connection,
    path: &Path,
    path_text: &str,
) -> Result<(TranscriptFileState, u64)> {
    let state = transcript_file_state(path)?;
    let cursor = read_file_cursor(connection, path_text)?;
    Ok((
        state,
        cursor.map_or(0, |cursor| cursor.resume_offset_for(&state)),
    ))
}

fn complete_ingestion(
    transaction: Transaction<'_>,
    path_text: &str,
    identity: FileIdentity,
    consumed_bytes: u64,
) -> Result<()> {
    write_file_cursor(&transaction, path_text, identity, consumed_bytes)?;
    transaction.commit()?;
    Ok(())
}

fn read_file_cursor(
    connection: &Connection,
    path_text: &str,
) -> rusqlite::Result<Option<FileCursor>> {
    connection
        .query_row(
            "SELECT device, inode, consumed_bytes FROM source_file WHERE path = ?1",
            [path_text],
            |row| file_cursor_at(row, 0),
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
