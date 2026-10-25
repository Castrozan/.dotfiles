import json
import os
from datetime import datetime, timezone
from pathlib import Path


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_record(path: Path) -> dict | None:
    try:
        record = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def write_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def remove_record(path: Path) -> None:
    path.unlink(missing_ok=True)


def revision_record_path(directory: Path, revision: str) -> Path:
    return directory / f"{revision}.json"


def revision_log_path(directory: Path, revision: str) -> Path:
    return directory / f"{revision}.log"


def read_text(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""
