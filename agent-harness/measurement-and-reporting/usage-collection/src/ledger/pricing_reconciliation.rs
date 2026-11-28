use anyhow::Result;
use rusqlite::{TransactionBehavior, params};

use super::UsageLedger;
use super::schema::{read_metadata, write_metadata};
use crate::pricing::PricingTable;
use crate::transcript::TokenCounts;

const PRICING_FINGERPRINT_KEY: &str = "pricing_fingerprint";

impl UsageLedger {
    pub fn reconcile_pricing(&mut self, pricing: &PricingTable) -> Result<bool> {
        if read_metadata(&self.connection, PRICING_FINGERPRINT_KEY)?.as_deref()
            == Some(pricing.fingerprint())
        {
            return Ok(false);
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        {
            let mut stored_entries = transaction.prepare(
                "SELECT entry_id, model, is_fast, input_tokens, output_tokens,
                    cache_creation_five_minute_tokens, cache_creation_one_hour_tokens,
                    cache_read_tokens, reported_cost_usd
                 FROM usage_entry",
            )?;
            let mut update_cost =
                transaction.prepare("UPDATE usage_entry SET cost_usd = ?2 WHERE entry_id = ?1")?;
            let mut rows = stored_entries.query([])?;
            while let Some(row) = rows.next()? {
                let model: String = row.get(1)?;
                let tokens = TokenCounts {
                    input: row.get::<_, i64>(3)? as u64,
                    output: row.get::<_, i64>(4)? as u64,
                    cache_creation_five_minute: row.get::<_, i64>(5)? as u64,
                    cache_creation_one_hour: row.get::<_, i64>(6)? as u64,
                    cache_read: row.get::<_, i64>(7)? as u64,
                };
                let cost_usd = pricing.usage_cost_usd(&model, row.get(2)?, &tokens, row.get(8)?);
                update_cost.execute(params![row.get::<_, i64>(0)?, cost_usd])?;
            }
        }
        write_metadata(&transaction, PRICING_FINGERPRINT_KEY, pricing.fingerprint())?;
        transaction.commit()?;
        Ok(true)
    }
}
