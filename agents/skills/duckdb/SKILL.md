---
name: duckdb
description: Query and manage the shared DuckDB persistent data store. Use when storing structured data, querying work history, tracking RIL items, logging decisions, or checking tool health across agents.
---

# DuckDB — Shared Persistent Data Store

All agents share a single DuckDB database at `~/.openclaw/shared/openclaw.duckdb`.

Use DuckDB for **structured, queryable data**. Use markdown for **narrative context and memory**.

## When to Use

| Data Type | Where |
|-----------|-------|
| Structured records (tickets, contacts, items) | DuckDB |
| Aggregations, counts, time-series | DuckDB |
| Cross-agent shared state | DuckDB |
| Decisions, preferences, patterns | MEMORY.md |
| Daily work logs, context notes | memory/*.md |
| Free-form notes, instructions | Markdown |

## Query Pattern

All queries use exec with duckdb CLI:

```bash
duckdb ~/.openclaw/shared/openclaw.duckdb "SELECT * FROM v_tool_health"
```

For multi-line SQL:

```bash
duckdb ~/.openclaw/shared/openclaw.duckdb <<'SQL'
SELECT agent_id, COUNT(*) as sessions, MAX(started_at) as last_active
FROM work_sessions
GROUP BY agent_id
ORDER BY last_active DESC;
SQL
```

## Tables

### work_sessions
Track what each agent worked on.

```sql
-- Log a session
INSERT INTO work_sessions (agent_id, task_summary)
VALUES ('silver', 'RIL inbox processing — 5 items reviewed');

-- Complete a session
UPDATE work_sessions SET ended_at = now(), outcome = 'done'
WHERE id = '<id>';

-- Recent work across agents
SELECT * FROM v_recent_work;
```

### ril_items
Track ReadItLater inbox items and processing status.

```sql
-- Register an item
INSERT INTO ril_items (file_path, title, source_type, author, relevance)
VALUES ('Tweet from X (2026-02-15).md', 'AI metrics thread', 'tweet', '@rryssf_', 'must-read');

-- Mark processed
UPDATE ril_items SET processed_at = now(), summary = 'Summary here', tags = ['ai', 'hallucination']
WHERE file_path = 'Tweet from X (2026-02-15).md';

-- Unprocessed items
SELECT * FROM v_unprocessed_ril;

-- Stats
SELECT source_type, COUNT(*) as total,
       COUNT(processed_at) as done,
       COUNT(*) - COUNT(processed_at) as pending
FROM ril_items GROUP BY source_type;
```

### decisions
Structured decision log with reasoning.

```sql
INSERT INTO decisions (agent_id, decision, reasoning, context)
VALUES ('silver', 'Use QMD over ClawVault', 'Our stack covers 80% of value, missing piece was discipline not tooling', 'RIL review of ClawVault tweet');
```

### tool_status
Track which tools work and when they were last verified.

```sql
-- Update tool status
INSERT INTO tool_status (tool_name, status, notes)
VALUES ('twikit-cli', 'degraded', 'tweet fetch broken (itemContent error), search works')
ON CONFLICT (tool_name) DO UPDATE SET status = excluded.status, notes = excluded.notes, last_tested = now();

-- Check health
SELECT * FROM v_tool_health;
```

### contacts
People context across platforms.

```sql
INSERT INTO contacts (name, handle, platform, context)
VALUES ('Pedro', '@sillydarket', 'twitter', 'ClawVault creator, OpenClaw memory tooling');
```

## Initialization

If the database doesn't exist, initialize it:

```bash
mkdir -p ~/.openclaw/shared
duckdb ~/.openclaw/shared/openclaw.duckdb < ~/openclaw/silver/projects/persistent-data-layer/init-duckdb.sql
```

## JSON Output

For parsing results in scripts:

```bash
duckdb ~/.openclaw/shared/openclaw.duckdb -json "SELECT * FROM tool_status"
```

## Export

```bash
duckdb ~/.openclaw/shared/openclaw.duckdb "COPY (SELECT * FROM ril_items) TO '~/.openclaw/shared/exports/ril.csv' (HEADER true)"
```
