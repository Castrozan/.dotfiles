use rusqlite::{Connection, Result};
use sha2::{Digest, Sha256};

use super::entry_queries::{
    StoredEntry, find_by_dedup_key, find_sidechain_counterpart, insert_entry, register_dedup_key,
    replace_entry,
};
use crate::transcript::{MessageIdentity, UsageEntry};

struct EntryKeys {
    dedup: i64,
    message: i64,
}

impl EntryKeys {
    fn for_identity(identity: &MessageIdentity) -> Self {
        let request = identity.request_id.as_deref().map_or_else(
            || "\u{0}".to_string(),
            |request_id| format!("request\u{1f}{request_id}"),
        );
        Self {
            dedup: stable_key(&format!(
                "message\u{1f}{}\u{1e}{request}",
                identity.message_id
            )),
            message: stable_key(&format!("message\u{1f}{}", identity.message_id)),
        }
    }
}

impl StoredEntry {
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
    let keys = EntryKeys::for_identity(identity);
    match find_kept_entry(connection, &keys, entry.is_sidechain)? {
        None => insert_identified_entry(connection, entry, cost_usd, &keys),
        Some(kept_entry) => {
            reconcile_with_kept_entry(connection, &kept_entry, entry, cost_usd, &keys)
        }
    }
}

fn find_kept_entry(
    connection: &Connection,
    keys: &EntryKeys,
    entry_is_sidechain: bool,
) -> Result<Option<StoredEntry>> {
    match find_by_dedup_key(connection, keys.dedup)? {
        Some(kept_entry) => Ok(Some(kept_entry)),
        None => find_sidechain_counterpart(connection, keys.message, entry_is_sidechain),
    }
}

fn insert_identified_entry(
    connection: &Connection,
    entry: &UsageEntry,
    cost_usd: f64,
    keys: &EntryKeys,
) -> Result<bool> {
    let entry_id = insert_entry(connection, entry, cost_usd, Some(keys.message))?;
    register_dedup_key(connection, keys.dedup, entry_id)?;
    Ok(true)
}

fn reconcile_with_kept_entry(
    connection: &Connection,
    kept_entry: &StoredEntry,
    entry: &UsageEntry,
    cost_usd: f64,
    keys: &EntryKeys,
) -> Result<bool> {
    register_dedup_key(connection, keys.dedup, kept_entry.entry_id)?;
    if !kept_entry.is_superseded_by(entry, cost_usd) {
        return Ok(false);
    }
    replace_entry(connection, kept_entry.entry_id, entry, cost_usd)?;
    Ok(true)
}

fn stable_key(text: &str) -> i64 {
    let digest = Sha256::digest(text.as_bytes());
    i64::from_le_bytes(
        digest[..8]
            .try_into()
            .expect("a sha256 digest holds eight bytes"),
    )
}
