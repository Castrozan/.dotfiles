mod entry_store;
mod ingestion;
mod pricing_reconciliation;
mod report;
mod schema;

use std::path::Path;
use std::time::Duration;

use anyhow::{Context, Result};
use rusqlite::Connection;

pub use ingestion::IngestionSummary;

const BUSY_TIMEOUT: Duration = Duration::from_secs(30);

pub struct UsageLedger {
    connection: Connection,
}

impl UsageLedger {
    pub fn open(ledger_path: &Path) -> Result<Self> {
        if let Some(directory) = ledger_path.parent() {
            std::fs::create_dir_all(directory)
                .with_context(|| format!("could not create {}", directory.display()))?;
        }
        let connection = Connection::open(ledger_path).with_context(|| {
            format!("could not open the usage ledger {}", ledger_path.display())
        })?;
        connection.busy_timeout(BUSY_TIMEOUT)?;
        schema::prepare_schema(&connection).context("could not prepare the usage ledger schema")?;
        Ok(Self { connection })
    }
}
