use rusqlite::{Result, Row};

use crate::transcript::TokenCounts;

pub fn integer_columns<const COUNT: usize>(
    row: &Row<'_>,
    first_column: usize,
) -> Result<[u64; COUNT]> {
    let mut values = [0u64; COUNT];
    for (offset, value) in values.iter_mut().enumerate() {
        *value = row.get::<_, i64>(first_column + offset)? as u64;
    }
    Ok(values)
}

pub fn token_counts_at(row: &Row<'_>, first_column: usize) -> Result<TokenCounts> {
    let [
        input,
        output,
        cache_creation_five_minute,
        cache_creation_one_hour,
        cache_read,
    ] = integer_columns::<5>(row, first_column)?;
    Ok(TokenCounts {
        input,
        output,
        cache_creation_five_minute,
        cache_creation_one_hour,
        cache_read,
    })
}
