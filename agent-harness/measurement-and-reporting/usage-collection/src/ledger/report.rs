use anyhow::Result;
use rusqlite::Row;

use super::UsageLedger;
use super::row_columns::integer_columns;
use crate::usage_totals::{DailyModelUsage, ModelUsageTotals};

const DAILY_MODEL_USAGE: &str = "SELECT usage_date, model, is_fast, SUM(input_tokens),
        SUM(output_tokens), SUM(cache_read_tokens),
        SUM(cache_creation_five_minute_tokens + cache_creation_one_hour_tokens),
        TOTAL(cost_usd)
     FROM usage_entry
     GROUP BY usage_date, model, is_fast
     ORDER BY usage_date, model, is_fast";
const FIRST_TOTAL_COLUMN: usize = 3;

impl UsageLedger {
    pub fn daily_model_usage(&self) -> Result<Vec<DailyModelUsage>> {
        let mut statement = self.connection.prepare(DAILY_MODEL_USAGE)?;
        let rows = statement.query_map([], daily_model_usage_row)?;
        Ok(rows.collect::<rusqlite::Result<_>>()?)
    }
}

fn daily_model_usage_row(row: &Row<'_>) -> rusqlite::Result<DailyModelUsage> {
    Ok(DailyModelUsage {
        usage_date: row.get(0)?,
        model: row.get(1)?,
        is_fast: row.get(2)?,
        totals: usage_totals_at(row, FIRST_TOTAL_COLUMN)?,
    })
}

fn usage_totals_at(row: &Row<'_>, first_column: usize) -> rusqlite::Result<ModelUsageTotals> {
    let [
        input_tokens,
        output_tokens,
        cache_read_input_tokens,
        cache_creation_input_tokens,
    ] = integer_columns::<4>(row, first_column)?;
    Ok(ModelUsageTotals {
        input_tokens,
        output_tokens,
        cache_read_input_tokens,
        cache_creation_input_tokens,
        cost_usd: row.get(first_column + 4)?,
    })
}
