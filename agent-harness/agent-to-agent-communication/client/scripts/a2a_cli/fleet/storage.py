"""Private SQLite connection and version-one schema initialization."""

import os
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS hosts (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agents (
    host TEXT, pane TEXT, session TEXT, data TEXT NOT NULL,
    PRIMARY KEY(host, pane, session));
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, host TEXT, pane TEXT, session TEXT,
    state TEXT, data TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(host, pane)
    WHERE state IN ('dispatching','dispatched','working','blocked',
                    'uncertain','reported_completed');
PRAGMA user_version=1;
"""


def prepare_file(path):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        stat = os.fstat(fd)
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ValueError("registry must be owned by this user and mode 0600")
    finally:
        os.close(fd)


def connect(path):
    path = Path(path).expanduser()
    prepare_file(path)
    db = sqlite3.connect(path, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA synchronous=FULL")
    if db.execute("PRAGMA user_version").fetchone()[0] not in (0, 1):
        db.close()
        raise ValueError("unsupported fleet registry schema")
    with db:
        db.executescript(SCHEMA)
    return db
