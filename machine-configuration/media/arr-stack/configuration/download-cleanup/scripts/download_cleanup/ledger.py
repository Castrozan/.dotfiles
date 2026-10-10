import json
import sqlite3
import time
from contextlib import contextmanager

from .domain import Media, torrent_hash


class Ledger:
    def __init__(self, path):
        self.path = str(path)
        with self.connection() as connection:
            connection.executescript(
                "CREATE TABLE IF NOT EXISTS downloads (app TEXT, media_id INTEGER, provider_id INTEGER, library_path TEXT, download_hash TEXT, content_path TEXT NOT NULL DEFAULT '', PRIMARY KEY(app,media_id,provider_id,library_path,download_hash));"
                "CREATE INDEX IF NOT EXISTS download_owners ON downloads(download_hash);"
                "CREATE TABLE IF NOT EXISTS jobs (app TEXT, media_id INTEGER, provider_id INTEGER, library_path TEXT, payload TEXT, next_attempt REAL NOT NULL DEFAULT 0, completed_at REAL, PRIMARY KEY(app,media_id,provider_id,library_path));"
            )

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA max_page_count=8192")
            with connection:
                yield connection
        finally:
            connection.close()

    def record_download(self, media, download_hash):
        download_hash = torrent_hash(download_hash)
        with self.connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO downloads(app,media_id,provider_id,library_path,download_hash) VALUES (?,?,?,?,?)",
                (*media.key, download_hash),
            )
            connection.execute(
                "UPDATE jobs SET next_attempt=0,completed_at=NULL WHERE app=? AND media_id=? AND provider_id=? AND library_path=?",
                media.key,
            )

    def enqueue(self, media):
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO jobs(app,media_id,provider_id,library_path,payload) VALUES (?,?,?,?,?) ON CONFLICT(app,media_id,provider_id,library_path) DO UPDATE SET next_attempt=0,completed_at=NULL",
                (*media.key, json.dumps(media.serialize())),
            )

    def pending(self, now=None):
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM jobs WHERE completed_at IS NULL AND next_attempt<=? ORDER BY next_attempt LIMIT 10",
                (time.time() if now is None else now,),
            ).fetchall()
        return [Media(**json.loads(row[0])) for row in rows]

    def downloads(self, media):
        with self.connection() as connection:
            return connection.execute(
                "SELECT download_hash,content_path FROM downloads WHERE app=? AND media_id=? AND provider_id=? AND library_path=? ORDER BY download_hash",
                media.key,
            ).fetchall()

    def owners(self, download_hash):
        with self.connection() as connection:
            return connection.execute(
                "SELECT DISTINCT app,media_id,provider_id,library_path FROM downloads WHERE download_hash=?",
                (download_hash,),
            ).fetchall()

    def remember_paths(self, media, torrents):
        with self.connection() as connection:
            for torrent in torrents:
                connection.execute(
                    "UPDATE downloads SET content_path=? WHERE app=? AND media_id=? AND provider_id=? AND library_path=? AND download_hash=?",
                    (torrent["content_path"], *media.key, torrent["hash"].lower()),
                )

    def retry(self, media):
        with self.connection() as connection:
            connection.execute(
                "UPDATE jobs SET next_attempt=? WHERE app=? AND media_id=? AND provider_id=? AND library_path=?",
                (time.time() + 30, *media.key),
            )

    def cancel(self, media):
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM jobs WHERE app=? AND media_id=? AND provider_id=? AND library_path=?",
                media.key,
            )

    def complete(self, media):
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM downloads WHERE app=? AND media_id=? AND provider_id=? AND library_path=?",
                media.key,
            )
            connection.execute(
                "UPDATE jobs SET completed_at=? WHERE app=? AND media_id=? AND provider_id=? AND library_path=?",
                (time.time(), *media.key),
            )
            connection.execute(
                "DELETE FROM jobs WHERE completed_at<?", (time.time() - 30 * 86400,)
            )
