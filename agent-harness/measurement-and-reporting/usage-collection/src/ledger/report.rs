use anyhow::Result;

use super::UsageLedger;
use crate::usage_totals::{DailyModelUsage, ModelUsageTotals};

impl UsageLedger {
    pub fn daily_model_usage(&self) -> Result<Vec<DailyModelUsage>> {
        let mut statement = self.connection.prepare(
            "SELECT usage_date, model, is_fast, SUM(input_tokens), SUM(output_tokens),
                SUM(cache_read_tokens),
                SUM(cache_creation_five_minute_tokens + cache_creation_one_hour_tokens),
                TOTAL(cost_usd)
             FROM usage_entry
             GROUP BY usage_date, model, is_fast
             ORDER BY usage_date, model, is_fast",
        )?;
        let rows = statement.query_map([], |row| {
            Ok(DailyModelUsage {
                usage_date: row.get(0)?,
                model: row.get(1)?,
                is_fast: row.get(2)?,
                totals: ModelUsageTotals {
                    input_tokens: row.get::<_, i64>(3)? as u64,
                    output_tokens: row.get::<_, i64>(4)? as u64,
                    cache_read_input_tokens: row.get::<_, i64>(5)? as u64,
                    cache_creation_input_tokens: row.get::<_, i64>(6)? as u64,
                    cost_usd: row.get(7)?,
                },
            })
        })?;
        Ok(rows.collect::<rusqlite::Result<_>>()?)
    }
}
