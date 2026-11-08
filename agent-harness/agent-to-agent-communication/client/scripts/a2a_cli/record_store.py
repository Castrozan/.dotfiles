from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .document_fields import InvalidPeerDocument

RECORD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def state_directory(name: str) -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / name


def record_path(directory: Path, name: str) -> Path:
    if not RECORD_NAME_PATTERN.match(name or ""):
        raise InvalidPeerDocument(f"{name!r} is not a record name")
    return directory / f"{name}.json"


def save_record(directory: Path, name: str, record: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = record_path(directory, name)
    file_descriptor, temporary_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as temporary_file:
        json.dump(record, temporary_file, indent=2, ensure_ascii=False)
    os.replace(temporary_name, destination)
    return destination


def load_record(directory: Path, name: str) -> dict:
    path = record_path(directory, name)
    if not path.is_file():
        raise InvalidPeerDocument(f"no record {name} in {directory}")
    return json.loads(path.read_text(encoding="utf-8"))


def all_records(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]
