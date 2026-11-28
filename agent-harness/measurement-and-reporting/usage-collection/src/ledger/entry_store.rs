use rusqlite::{Connection, OptionalExtension, Result, Row, params};
use sha2::{Digest, Sha256};

use crate::transcript::{MessageIdentity, UsageEntry};

const STORED_ENTRY_COLUMNS: &str = "entry_id, is_sidechain,
    input_tokens + output_tokens + cache_creation_five_minute_tokens
        + cache_creation_one_hour_tokens + cache_read_tokens,
    cost_usd";

struct StoredEntry {
    entry_id: i64,
    is_sidechain: bool,
    token_total: u64,
    cost_usd: f64,
}

impl StoredEntry {
    fn from_row(row: &Row<'_>) -> Result<Self> {
        Ok(Self {
            entry_id: row.get(0)?,
            is_sidechain: row.get(1)?,
            token_total: row.get::<_, i64>(2)? as u64,
            cost_usd: row.get(3)?,
        })
    }

    fn is_superseded_by(&self, entry: &UsageEntry, entry_cost_usd: f64) -> bool {
        if self.is_sidechain != entry.is_sidechain {
            return self.is_sidechain;
        }
        let entry_token_total = entry.tokens.total();
        if entry_token_total != self.token_total {
            return entry_token_total > self.token_total;
        }
        entry_cost_usd > self.cost_usd
    }
}

pub fn record_entry(connection: &Connection, entry: &UsageEntry, cost_usd: f64) -> Result<bool> {
    let Some(identity) = &entry.identity else {
        insert_entry(connection, entry, cost_usd, None)?;
        return Ok(true);
    };
    let dedup_key = identity_key(identity);
    let message_key = stable_key(&format!("message\u{1f}{}", identity.message_id));
    let kept_entry = match find_by_dedup_key(connection, dedup_key)? {
        Some(kept_entry) => Some(kept_entry),
        None => find_sidechain_counterpart(connection, message_key, entry.is_sidechain)?,
    };
    let Some(kept_entry) = kept_entry else {
        let entry_id = insert_entry(connection, entry, cost_usd, Some(message_key))?;
        register_dedup_key(connection, dedup_key, entry_id)?;
        return Ok(true);
    };
    register_dedup_key(connection, dedup_key, kept_entry.entry_id)?;
    if !kept_entry.is_superseded_by(entry, cost_usd) {
        return Ok(false);
    }
    replace_entry(connection, kept_entry.entry_id, entry, cost_usd)?;
    Ok(true)
}

fn register_dedup_key(connection: &Connection, dedup_key: i64, entry_id: i64) -> Result<()> {
    connection
        .prepare_cached("INSERT OR IGNORE INTO entry_key (dedup_key, entry_id) VALUES (?1, ?2)")?
        .execute(params![dedup_key, entry_id])?;
    Ok(())
}

fn identity_key(identity: &MessageIdentity) -> i64 {
    let request = identity.request_id.as_deref().map_or_else(
        || "\u{0}".to_string(),
        |request_id| format!("request\u{1f}{request_id}"),
    );
    stable_key(&format!(
        "message\u{1f}{}\u{1e}{request}",
        identity.message_id
    ))
}

fn stable_key(text: &str) -> i64 {
    let digest = Sha256::digest(text.as_bytes());
    i64::from_le_bytes(
        digest[..8]
            .try_into()
            .expect("a sha256 digest holds eight bytes"),
    )
}

fn find_by_dedup_key(connection: &Connection, dedup_key: i64) -> Result<Option<StoredEntry>> {
    connection
        .prepare_cached(&format!(
            "SELECT {STORED_ENTRY_COLUMNS} FROM usage_entry
             WHERE entry_id = (SELECT entry_id FROM entry_key WHERE dedup_key = ?1)"
        ))?
        .query_row([dedup_key], StoredEntry::from_row)
        .optional()
}

fn find_sidechain_counterpart(
    connection: &Connection,
    message_key: i64,
    entry_is_sidechain: bool,
) -> Result<Option<StoredEntry>> {
    connection
        .prepare_cached(&format!(
            "SELECT {STORED_ENTRY_COLUMNS} FROM usage_entry
             WHERE message_key = ?1 AND (?2 OR is_sidechain)
             ORDER BY entry_id LIMIT 1"
        ))?
        .query_row(
            params![message_key, entry_is_sidechain],
            StoredEntry::from_row,
        )
        .optional()
}

fn insert_entry(
    connection: &Connection,
    entry: &UsageEntry,
    cost_usd: f64,
    message_key: Option<i64>,
) -> Result<i64> {
    connection
        .prepare_cached(
            "INSERT INTO usage_entry (message_key, is_sidechain, usage_date, model,
                is_fast, input_tokens, output_tokens, cache_creation_five_minute_tokens,
                cache_creation_one_hour_tokens, cache_read_tokens, reported_cost_usd, cost_usd)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
        )?
        .execute(params![
            message_key,
            entry.is_sidechain,
            entry.usage_date,
            entry.model,
            entry.is_fast,
            entry.tokens.input as i64,
            entry.tokens.output as i64,
            entry.tokens.cache_creation_five_minute as i64,
            entry.tokens.cache_creation_one_hour as i64,
            entry.tokens.cache_read as i64,
            entry.reported_cost_usd,
            cost_usd,
        ])?;
    Ok(connection.last_insert_rowid())
}

fn replace_entry(
    connection: &Connection,
    entry_id: i64,
    entry: &UsageEntry,
    cost_usd: f64,
) -> Result<()> {
    connection
        .prepare_cached(
            "UPDATE usage_entry SET is_sidechain = ?2, usage_date = ?3, model = ?4, is_fast = ?5,
                input_tokens = ?6, output_tokens = ?7, cache_creation_five_minute_tokens = ?8,
                cache_creation_one_hour_tokens = ?9, cache_read_tokens = ?10,
                reported_cost_usd = ?11, cost_usd = ?12
             WHERE entry_id = ?1",
        )?
        .execute(params![
            entry_id,
            entry.is_sidechain,
            entry.usage_date,
            entry.model,
            entry.is_fast,
            entry.tokens.input as i64,
            entry.tokens.output as i64,
            entry.tokens.cache_creation_five_minute as i64,
            entry.tokens.cache_creation_one_hour as i64,
            entry.tokens.cache_read as i64,
            entry.reported_cost_usd,
            cost_usd,
        ])?;
    Ok(())
}
