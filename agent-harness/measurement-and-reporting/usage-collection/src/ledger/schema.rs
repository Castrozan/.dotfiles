use rusqlite::{Connection, OptionalExtension, Result, params};

const SCHEMA_VERSION_KEY: &str = "schema_version";
const LEDGER_SCHEMA_VERSION: &str = "1";

const CREATE_METADATA_TABLE: &str =
    "CREATE TABLE IF NOT EXISTS ledger_metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL)";

const RECREATE_LEDGER_TABLES: &str = "
    DROP TABLE IF EXISTS source_file;
    DROP TABLE IF EXISTS entry_key;
    DROP TABLE IF EXISTS usage_entry;
    CREATE TABLE source_file (
        path TEXT PRIMARY KEY,
        device INTEGER NOT NULL,
        inode INTEGER NOT NULL,
        consumed_bytes INTEGER NOT NULL
    );
    CREATE TABLE usage_entry (
        entry_id INTEGER PRIMARY KEY,
        message_key INTEGER,
        is_sidechain INTEGER NOT NULL,
        usage_date TEXT NOT NULL,
        model TEXT NOT NULL,
        is_fast INTEGER NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        cache_creation_five_minute_tokens INTEGER NOT NULL,
        cache_creation_one_hour_tokens INTEGER NOT NULL,
        cache_read_tokens INTEGER NOT NULL,
        reported_cost_usd REAL,
        cost_usd REAL NOT NULL
    );
    CREATE INDEX usage_entry_by_message ON usage_entry (message_key);
    CREATE TABLE entry_key (
        dedup_key INTEGER PRIMARY KEY,
        entry_id INTEGER NOT NULL REFERENCES usage_entry (entry_id)
    ) WITHOUT ROWID;
    DELETE FROM ledger_metadata;
";

pub fn prepare_schema(connection: &Connection) -> Result<()> {
    use_write_ahead_journal(connection)?;
    connection.execute(CREATE_METADATA_TABLE, [])?;
    if read_metadata(connection, SCHEMA_VERSION_KEY)?.as_deref() == Some(LEDGER_SCHEMA_VERSION) {
        return Ok(());
    }
    recreate_ledger_tables(connection)
}

fn use_write_ahead_journal(connection: &Connection) -> Result<()> {
    connection.pragma_update(None, "journal_mode", "WAL")?;
    connection.pragma_update(None, "synchronous", "NORMAL")
}

fn recreate_ledger_tables(connection: &Connection) -> Result<()> {
    connection.execute_batch(RECREATE_LEDGER_TABLES)?;
    write_metadata(connection, SCHEMA_VERSION_KEY, LEDGER_SCHEMA_VERSION)
}

pub fn read_metadata(connection: &Connection, name: &str) -> Result<Option<String>> {
    connection
        .query_row(
            "SELECT value FROM ledger_metadata WHERE name = ?1",
            [name],
            |row| row.get(0),
        )
        .optional()
}

pub fn write_metadata(connection: &Connection, name: &str, value: &str) -> Result<()> {
    connection.execute(
        "INSERT INTO ledger_metadata (name, value) VALUES (?1, ?2)
         ON CONFLICT (name) DO UPDATE SET value = excluded.value",
        params![name, value],
    )?;
    Ok(())
}
