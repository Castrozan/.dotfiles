import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


RUN_STATUS_FILENAME = "status.json"
PUBLICATION_FILENAME = "publication.json"


PREVIOUS_TOPICS = (
    ("military-bat-bombs", "Military bat bombs", "WE83gO4lIfs"),
    ("dead-salmon-brain-scan", "Dead salmon brain scan", "mTuwisp5jr8"),
    ("paper-folding-moon", "Paper folding to the Moon", "jbCl-QMs0M0"),
    ("ice-cream-history", "History of ice cream", None),
    ("zipper-failure", "Zipper failure mechanism", None),
    ("dotfiles-repository", "Dotfiles repository explainer", None),
)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def read_document(path):
    return json.loads(Path(path).read_text())


def write_document(path, document):
    path = Path(path)
    temporary = path.with_suffix(".temporary")
    temporary.write_text(json.dumps(document, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def topic_key(value):
    key = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not key or len(key) > 120:
        raise ValueError("Invalid topic key")
    return key


class TopicStore:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.connection = sqlite3.connect(directory / "topics.sqlite")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS topics "
            "(topic_key TEXT PRIMARY KEY, title TEXT NOT NULL, "
            "summary TEXT NOT NULL, run_id TEXT UNIQUE, status TEXT NOT NULL, "
            "video_id TEXT UNIQUE, created_at TEXT NOT NULL)"
        )
        with self.connection:
            self.connection.executemany(
                "INSERT OR IGNORE INTO topics VALUES (?, ?, ?, NULL, ?, ?, ?)",
                [
                    (
                        key,
                        title,
                        title,
                        "published" if video else "retired",
                        video,
                        timestamp(),
                    )
                    for key, title, video in PREVIOUS_TOPICS
                ],
            )

    def history(self):
        return [dict(row) for row in self.connection.execute("SELECT * FROM topics")]

    def reserve(self, proposal, run_id):
        key = topic_key(proposal["topic_key"])
        title = proposal["title"].strip()
        summary = proposal["summary"].strip()
        if not title or len(summary) < 30:
            raise ValueError("A title and specific topic summary are required")
        if self.topic_exists(key, title):
            raise ValueError("Topic already used or reserved")
        with self.connection:
            self.connection.execute(
                "INSERT INTO topics VALUES (?, ?, ?, ?, 'reserved', NULL, ?)",
                (key, title, summary, run_id, timestamp()),
            )
        return key

    def topic_exists(self, key, title):
        return any(
            previous["topic_key"] == key
            or topic_key(previous["title"]) == topic_key(title)
            for previous in self.history()
        )

    def reservation(self, run_id, key):
        row = self.connection.execute(
            "SELECT * FROM topics WHERE run_id=? AND topic_key=? AND status='reserved'",
            (run_id, topic_key(key)),
        ).fetchone()
        if row is None:
            raise ValueError("This run must own the reserved topic")
        return dict(row)

    def publish(self, run_id, video_id):
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE topics SET status='published', video_id=? WHERE run_id=? AND status='reserved'",
                (video_id, run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Expected exactly one reserved topic for this run")
