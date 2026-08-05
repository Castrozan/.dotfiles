import sqlite3
import subprocess
import sys
from pathlib import Path

OPENCODE_SESSION_DATABASE = (
    Path.home() / ".local" / "share" / "opencode" / "opencode.db"
)
MOST_RECENTLY_UPDATED_SESSION_FOR_DIRECTORY = (
    "select id from session where directory = ? order by time_updated desc limit 1"
)


def working_directory_of_process(process_identifier: int) -> Path | None:
    if sys.platform.startswith("linux"):
        try:
            return Path(f"/proc/{process_identifier}/cwd").resolve()
        except OSError:
            return None
    open_files_listing = subprocess.run(
        ["lsof", "-a", "-d", "cwd", "-p", str(process_identifier), "-Fn"],
        capture_output=True,
        text=True,
        check=False,
    )
    for listing_line in open_files_listing.stdout.splitlines():
        if listing_line.startswith("n"):
            return Path(listing_line[1:])
    return None


def opencode_session_identifier_for_process(
    process_identifier: int,
    session_database: Path = OPENCODE_SESSION_DATABASE,
) -> str | None:
    if not session_database.exists():
        return None
    harness_working_directory = working_directory_of_process(process_identifier)
    if harness_working_directory is None:
        return None
    try:
        session_database_connection = sqlite3.connect(
            f"file:{session_database}?mode=ro", uri=True, timeout=1
        )
        try:
            most_recent_session = session_database_connection.execute(
                MOST_RECENTLY_UPDATED_SESSION_FOR_DIRECTORY,
                (str(harness_working_directory),),
            ).fetchone()
        finally:
            session_database_connection.close()
    except sqlite3.Error:
        return None
    return most_recent_session[0] if most_recent_session else None
