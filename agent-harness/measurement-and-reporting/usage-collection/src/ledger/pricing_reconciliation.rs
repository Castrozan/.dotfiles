use anyhow::Result;
use rusqlite::{Connection, Row, TransactionBehavior, params};

use super::UsageLedger;
use super::row_columns::token_counts_at;
use super::schema::{read_metadata, write_metadata};
use crate::pricing::PricingTable;

const PRICING_FINGERPRINT_KEY: &str = "pricing_fingerprint";
const STORED_PRICING_INPUTS: &str = "SELECT entry_id, model, is_fast, reported_cost_usd,
        input_tokens, output_tokens, cache_creation_five_minute_tokens,
        cache_creation_one_hour_tokens, cache_read_tokens
     FROM usage_entry";
const FIRST_TOKEN_COLUMN: usize = 4;

impl UsageLedger {
    pub fn reconcile_pricing(&mut self, pricing: &PricingTable) -> Result<bool> {
        if self.prices_with(pricing)? {
            return Ok(false);
        }
        self.reprice_entries(pricing)?;
        Ok(true)
    }

    fn prices_with(&self, pricing: &PricingTable) -> Result<bool> {
        let stored_fingerprint = read_metadata(&self.connection, PRICING_FINGERPRINT_KEY)?;
        Ok(stored_fingerprint.as_deref() == Some(pricing.fingerprint()))
    }

    fn reprice_entries(&mut self, pricing: &PricingTable) -> Result<()> {
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        write_repriced_costs(&transaction, pricing)?;
        write_metadata(&transaction, PRICING_FINGERPRINT_KEY, pricing.fingerprint())?;
        transaction.commit()?;
        Ok(())
    }
}

fn write_repriced_costs(connection: &Connection, pricing: &PricingTable) -> rusqlite::Result<()> {
    let mut update_cost =
        connection.prepare("UPDATE usage_entry SET cost_usd = ?2 WHERE entry_id = ?1")?;
    for (entry_id, cost_usd) in repriced_costs(connection, pricing)? {
        update_cost.execute(params![entry_id, cost_usd])?;
    }
    Ok(())
}

fn repriced_costs(
    connection: &Connection,
    pricing: &PricingTable,
) -> rusqlite::Result<Vec<(i64, f64)>> {
    let mut stored_inputs = connection.prepare(STORED_PRICING_INPUTS)?;
    stored_inputs
        .query_map([], |row| repriced_cost(row, pricing))?
        .collect()
}

fn repriced_cost(row: &Row<'_>, pricing: &PricingTable) -> rusqlite::Result<(i64, f64)> {
    let (entry_id, model, is_fast, reported_cost_usd) = pricing_identity(row)?;
    let tokens = token_counts_at(row, FIRST_TOKEN_COLUMN)?;
    Ok((
        entry_id,
        pricing.usage_cost_usd(&model, is_fast, &tokens, reported_cost_usd),
    ))
}

fn pricing_identity(row: &Row<'_>) -> rusqlite::Result<(i64, String, bool, Option<f64>)> {
    Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?))
}
